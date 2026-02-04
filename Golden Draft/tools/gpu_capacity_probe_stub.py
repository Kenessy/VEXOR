import argparse

CONTRACT_PATH_REL_GOLDEN_DRAFT = "docs/gpu/objective_contract_v1.md"
CONTRACT_REPO_PATH = "Golden Draft/docs/gpu/objective_contract_v1.md"


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="gpu_capacity_probe_stub",
        formatter_class=argparse.RawTextHelpFormatter,
        description=(
            "Not implemented; see VRA-32.\n"
            f"Contract (relative to Golden Draft/): {CONTRACT_PATH_REL_GOLDEN_DRAFT}\n"
            f"Repo path: {CONTRACT_REPO_PATH}"
        ),
        epilog=f"See {CONTRACT_PATH_REL_GOLDEN_DRAFT}",
    )
    parser.parse_args()
    print("Not implemented; see VRA-32.")
    print(f"Contract (relative to Golden Draft/): {CONTRACT_PATH_REL_GOLDEN_DRAFT}")
    print(f"Repo path: {CONTRACT_REPO_PATH}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
