#!/usr/bin/env python3
"""Lists the container images running in every DOME cluster (sbx, dev, dev2, prd)
via kubectl, and writes one CSV per environment plus an images.xlsx report
with the partner owning each component."""
import argparse
import json
import csv
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

SCRIPT_DIR = Path(__file__).resolve().parent

KUBECONFIG_TEMPLATE_ENV = "KUBECONFIG_TEMPLATE"
ENVIRONMENTS = ["sbx", "dev", "dev2", "prd"]
ENV_LABELS = {"sbx": "Sandbox", "dev": "Dev", "dev2": "Dev2", "prd": "Prod"}

DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "output"
DEFAULT_PARTNERS_CSV = SCRIPT_DIR / "components-partner.csv"

DEFAULT_KUBECONFIG_TEMPLATE = "~/.kube/dome/{env}/kubeconfig.yaml"
EXAMPLE_TEMPLATE = "/path/to/kubeconfigs/{env}/kubeconfig.yaml"

USAGE_EXAMPLES = (
    "The kubeconfig template is a path containing the {env} placeholder, which is\n"
    f"replaced with each environment name ({', '.join(ENVIRONMENTS)}). It is taken from,\n"
    "in order of precedence:\n"
    "  1. the --kubeconfig-template option\n"
    f"  2. the {KUBECONFIG_TEMPLATE_ENV} environment variable\n"
    f"  3. the default: {DEFAULT_KUBECONFIG_TEMPLATE}\n"
    "\n"
    "Kubeconfig files contain cluster credentials: keep them OUTSIDE this repository.\n"
    "\n"
    "examples:\n"
    f"  %(prog)s                     # uses {DEFAULT_KUBECONFIG_TEMPLATE}\n"
    "\n"
    f"  %(prog)s --kubeconfig-template {EXAMPLE_TEMPLATE}\n"
    "\n"
    f"  export {KUBECONFIG_TEMPLATE_ENV}={EXAMPLE_TEMPLATE}   # e.g. in ~/.bashrc\n"
    "  %(prog)s\n"
)


def no_kubeconfig_found_message(prog: str, template: str, source: str,
                                looked_up: dict[str, Path]) -> str:
    listing = "\n".join(f"  [{env}] {path}" for env, path in looked_up.items())
    return (
        "ERROR: no kubeconfig file found.\n"
        "\n"
        f"Template used: {template}  (from {source})\n"
        "Files looked up:\n"
        f"{listing}\n"
        "\n"
        f"This script needs one kubeconfig file per environment ({', '.join(ENVIRONMENTS)}).\n"
        "Either put them in the paths above, or tell the script where they are with a\n"
        "path template containing the {env} placeholder, in one of these two ways:\n"
        "\n"
        "  1. command-line option:\n"
        f"       {prog} --kubeconfig-template {EXAMPLE_TEMPLATE}\n"
        "\n"
        "  2. environment variable (e.g. in ~/.bashrc):\n"
        f"       export {KUBECONFIG_TEMPLATE_ENV}={EXAMPLE_TEMPLATE}\n"
        "\n"
        "Kubeconfig files contain cluster credentials: keep them OUTSIDE this repository.\n"
        "Run with --help for all options."
    )

# k8s namespace → CSV namespace when the names differ
NS_ALIASES: dict[str, str] = {
    "cs-identity":        "customer service",
    "chatbot":            "customer service",
    "knowledgebase":      "customer service",
    "zammad":             "customer service",
    "zammad2":            "customer service",
    "search-engine":      "search",
    "analytics":          "reporting & analytics",
    "dome-certification": "products compliance",
}


def _norm(s: str) -> str:
    """Strips separators for fuzzy comparisons (e.g. tm-forum-api → tmforumapi)."""
    return s.lower().replace("-", "").replace("_", "").replace(" ", "")


def load_partners(path: str):
    # (csv_ns, comp_lower) → (partner, original_comp_name)
    by_ns_comp: dict[tuple[str, str], tuple[str, str]] = {}
    # comp_lower → (partner, original_comp_name)  (global)
    by_comp:    dict[str, tuple[str, str]] = {}
    by_ns:      dict[str, str] = {}               # csv_ns → partner (fallback)
    multi_ns:   set[str] = set()                  # csv_ns with more than one partner
    _ns_partners: dict[str, set[str]] = {}

    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            ns      = row["Namespace"].strip()
            comp    = row["Component"].strip()
            partner = row["Partner"].strip()
            key     = comp.lower()
            by_ns_comp[(ns, key)] = (partner, comp)
            by_comp.setdefault(key, (partner, comp))
            by_ns.setdefault(ns, partner)
            _ns_partners.setdefault(ns, set()).add(partner)

    multi_ns = {ns for ns, pts in _ns_partners.items() if len(pts) > 1}
    return by_ns_comp, by_comp, by_ns, multi_ns


def lookup_partner(
    by_ns_comp: dict, by_comp: dict, by_ns: dict, multi_ns: set,
    k8s_ns: str, candidates: list[str],
) -> tuple[str, str]:
    """Returns (partner, component_name_from_csv). component is empty when the
    match is only at namespace level, or when there is no match."""
    csv_ns = NS_ALIASES.get(k8s_ns, k8s_ns)

    # 1. Exact match (csv_ns, component)
    for c in candidates:
        if c and (csv_ns, c.lower()) in by_ns_comp:
            partner, comp = by_ns_comp[(csv_ns, c.lower())]
            return partner, comp

    # 2. Namespace fallback, only for namespaces with a single partner (avoids multi-partner conflicts)
    if csv_ns in by_ns and csv_ns not in multi_ns:
        return by_ns[csv_ns], ""

    # 3. Global exact match on the component name
    for c in candidates:
        if c and c.lower() in by_comp:
            partner, comp = by_comp[c.lower()]
            return partner, comp

    # 4. Fuzzy match: the normalized component name is a substring of the candidate
    for c in candidates:
        nc = _norm(c)
        for comp_key, (partner, comp) in by_comp.items():
            nk = _norm(comp_key)
            if len(nk) >= 6 and nk in nc:
                return partner, comp

    return "", ""


def get_pods_json(kubeconfig: str) -> dict:
    result = subprocess.run(
        ["kubectl", "--kubeconfig", kubeconfig, "get", "pods", "--all-namespaces", "-o", "json"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def get_argocd_apps(kubeconfig: str) -> dict[tuple[str, str], str]:
    """Returns {(dest_namespace, instance_or_release): argocd_app_name}.
    On error (e.g. ArgoCD not installed) returns an empty dict."""
    try:
        result = subprocess.run(
            ["kubectl", "--kubeconfig", kubeconfig,
             "get", "applications", "-n", "argocd", "-o", "json"],
            capture_output=True, text=True, check=True,
        )
        data = json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return {}

    mapping: dict[tuple[str, str], str] = {}
    for app in data["items"]:
        app_name = app["metadata"]["name"]
        dest_ns  = app["spec"]["destination"].get("namespace", "")
        # In most cases the Application name matches the instance/release label
        mapping[(dest_ns, app_name)] = app_name
    return mapping


def parse_image(image: str) -> tuple[str, str]:
    repo, _, tag = image.rpartition(":")
    if "/" in tag or not tag:
        return image, ""
    return repo, tag


def tag_issue(tag: str) -> str:
    if not tag:
        return "NO TAG"
    if tag.lower() == "latest":
        return "LATEST"
    return ""


def extract_rows(
    data: dict, argocd_apps: dict[tuple[str, str], str]
) -> tuple[list[list[str]], list[list[str]], list[str]]:
    """Returns (rows, candidates, app_names).
    candidates: labels used to look up the partner in the CSV.
    app_names:  ArgoCD Application associated with the pod."""
    rows:      list[list[str]] = []
    candidates: list[list[str]] = []
    app_names:  list[str]       = []

    for pod in data["items"]:
        ns      = pod["metadata"]["namespace"]
        podname = pod["metadata"]["name"]
        labels  = pod["metadata"].get("labels", {})

        instance = labels.get("app.kubernetes.io/instance", "")
        release  = labels.get("release", "")
        argocd_app = (argocd_apps.get((ns, instance))
                      or argocd_apps.get((ns, release))
                      or "")

        # Pod from a Helm release not managed by ArgoCD
        helm_id   = instance or release
        is_manual = bool(helm_id and not argocd_app)
        app_name  = argocd_app or (helm_id if is_manual else "")

        # Candidates for the partner lookup: ArgoCD app first (most reliable)
        cands = [
            argocd_app,
            labels.get("component", ""),                   # Helm chart component (e.g. BAE)
            labels.get("app.kubernetes.io/name", ""),      # standard k8s name
            labels.get("app", ""),                         # legacy
            labels.get("app.kubernetes.io/component", ""),
        ]
        service = (labels.get("app.kubernetes.io/name")
                   or labels.get("app")
                   or labels.get("component")
                   or "")

        resolved = {
            cs["name"]: cs.get("image", "")
            for cs in pod.get("status", {}).get("containerStatuses", [])
        }

        for c in pod["spec"]["containers"]:
            repo, tag = parse_image(c["image"])
            rows.append([ns, podname, service, c["name"], repo, tag,
                         resolved.get(c["name"], ""), tag_issue(tag)])
            candidates.append(cands)
            app_names.append((app_name, is_manual))

    return rows, candidates, app_names


CSV_HEADER  = ["namespace", "pod", "service", "container",
               "image_declared", "tag_declared", "image_resolved", "tag_issue"]

XLSX_HEADER = ["namespace", "application", "company", "pod", "service", "container",
               "image_declared", "tag_declared", "image_resolved", "tag_issue"]

HEADER_FILL = PatternFill(fill_type="solid", fgColor="2F75B6")
HEADER_FONT = Font(bold=True, color="FFFFFF")
MANUAL_FILL = PatternFill(fill_type="solid", fgColor="FFD966")  # amber yellow


def write_csv(rows: list[list[str]], output: Path) -> None:
    with open(output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)
        writer.writerows(rows)


def write_xlsx(
    env_data: dict[str, tuple],
    partners_data: tuple,
    output: Path,
) -> None:
    by_ns_comp, by_comp, by_ns, multi_ns = partners_data
    wb = Workbook()
    wb.remove(wb.active)

    for env, (rows, candidates, app_names) in env_data.items():
        ws = wb.create_sheet(title=ENV_LABELS.get(env, env))
        ws.append(XLSX_HEADER)
        for cell in ws[1]:
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL
            cell.alignment = Alignment(horizontal="center")
        for row, cands, (app_name, is_manual) in zip(rows, candidates, app_names):
            ns         = row[0]
            company, _ = lookup_partner(by_ns_comp, by_comp, by_ns, multi_ns, ns, cands)
            label      = f"[manual] {app_name}" if is_manual else app_name
            ws.append([ns, label, company] + row[1:])
            if is_manual:
                for cell in ws[ws.max_row]:
                    cell.fill = MANUAL_FILL
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = max(len(str(c.value or "")) for c in col) + 2
        ws.auto_filter.ref = ws.dimensions

    wb.save(output)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=USAGE_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--kubeconfig-template",
        metavar="TEMPLATE",
        help=f"path of the kubeconfig files, with {{env}} as placeholder for the environment "
             f"(default: ${KUBECONFIG_TEMPLATE_ENV} if set, otherwise {DEFAULT_KUBECONFIG_TEMPLATE})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="directory where a timestamped subdirectory with the reports is created "
             "(default: %(default)s)",
    )
    parser.add_argument(
        "--partners-csv",
        type=Path,
        default=DEFAULT_PARTNERS_CSV,
        help="CSV mapping namespace/component to partner (default: %(default)s)",
    )
    args = parser.parse_args()
    args.prog = parser.prog

    # precedence: CLI option > environment variable > default
    if args.kubeconfig_template:
        args.kubeconfig_template_source = "--kubeconfig-template option"
    elif os.environ.get(KUBECONFIG_TEMPLATE_ENV):
        args.kubeconfig_template = os.environ[KUBECONFIG_TEMPLATE_ENV]
        args.kubeconfig_template_source = f"${KUBECONFIG_TEMPLATE_ENV} variable"
    else:
        args.kubeconfig_template = DEFAULT_KUBECONFIG_TEMPLATE
        args.kubeconfig_template_source = "default"

    template, source = args.kubeconfig_template, args.kubeconfig_template_source
    if "{env}" not in template:
        sys.exit(
            f"ERROR: the kubeconfig template {template!r} (from {source}) does not contain "
            "the {env} placeholder,\nso every environment would use the same kubeconfig.\n"
            f"Example: {EXAMPLE_TEMPLATE}"
        )
    try:
        template.format(env=ENVIRONMENTS[0])
    except (KeyError, IndexError, ValueError):
        sys.exit(
            f"ERROR: invalid kubeconfig template {template!r} (from {source}): "
            "the only allowed placeholder is {env}.\n"
            f"Example: {EXAMPLE_TEMPLATE}"
        )
    if not args.partners_csv.is_file():
        sys.exit(f"ERROR: partners CSV not found: {args.partners_csv}")
    return args


def resolve_kubeconfigs(prog: str, template: str, source: str) -> dict[str, Path]:
    """Returns {env: kubeconfig} for the environments whose file exists.
    Exits with an error if none exists."""
    print(f"Kubeconfig template: {template}  (from {source})", flush=True)
    kubeconfigs = {env: Path(os.path.expandvars(template.format(env=env))).expanduser()
                   for env in ENVIRONMENTS}
    missing = {env: path for env, path in kubeconfigs.items() if not path.is_file()}

    if len(missing) == len(kubeconfigs):
        sys.exit(no_kubeconfig_found_message(prog, template, source, missing))
    for env, path in missing.items():
        print(f"  [{env}] SKIPPED: kubeconfig not found: {path}", file=sys.stderr)

    return {env: path for env, path in kubeconfigs.items() if env not in missing}


def main():
    args = parse_args()
    kubeconfigs = resolve_kubeconfigs(args.prog, args.kubeconfig_template,
                                      args.kubeconfig_template_source)
    partners_data = load_partners(args.partners_csv)

    outdir = args.output_dir / datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
    outdir.mkdir(parents=True)
    print(f"Output directory: {outdir}/")

    env_data: dict[str, tuple] = {}

    for env, kubeconfig in kubeconfigs.items():
        print(f"  [{env}] querying kubectl...", end=" ", flush=True)
        try:
            pods_data   = get_pods_json(kubeconfig)
            argocd_apps = get_argocd_apps(kubeconfig)
        except subprocess.CalledProcessError as e:
            print(f"FAILED\n    kubectl error: {e.stderr.strip()}", file=sys.stderr)
            continue

        rows, candidates, app_names = extract_rows(pods_data, argocd_apps)
        env_data[env] = (rows, candidates, app_names)
        write_csv(rows, outdir / f"{env}.csv")
        print(f"{len(rows)} rows -> {outdir}/{env}.csv")

    if env_data:
        xlsx_path = outdir / "images.xlsx"
        write_xlsx(env_data, partners_data, xlsx_path)
        print(f"  xlsx -> {xlsx_path}")


if __name__ == "__main__":
    main()
