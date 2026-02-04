import argparse

CONTRACT_PATH = "docs/gpu/objective_contract_v1.md"


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="gpu_capacity_probe_stub",
        description=f"Not implemented. Contract: {CONTRACT_PATH}",
        epilog=f"See {CONTRACT_PATH}",
    )
    parser.parse_args()
    print(f"Not implemented; see VRA-32. Contract: {CONTRACT_PATH}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

