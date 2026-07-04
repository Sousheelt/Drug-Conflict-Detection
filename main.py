from __future__ import annotations

import argparse
from pathlib import Path

from model import HealthcareModel
from utils import logger


def main():
    parser = argparse.ArgumentParser(description="Drug Conflict Detection System")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["smart", "conflict-prone"],
        default="smart",
        help="Doctor mode: 'smart' (avoids conflicts) or 'conflict-prone' (creates conflicts for demo)"
    )
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent
    data_dir = base_dir
    output_dir = base_dir / "output"

    print(f"\n🏥 Running simulation in {args.mode.upper()} mode...")
    model = HealthcareModel(data_dir=data_dir, doctor_mode=args.mode)
    model.run(steps=1)

    # Save results
    out_csv = output_dir / "conflicts.csv"
    model.save_conflicts_csv(out_csv)

    # Console summary
    df = model.conflicts_dataframe()
    total_conflicts = len(df)
    by_sev = df["severity"].value_counts().to_dict() if total_conflicts else {}

    print("\n=== Simulation Summary ===")
    print(f"Mode: {args.mode.upper()}")
    print(f"Total prescriptions: {model.total_prescriptions}")
    print(f"Conflicts detected: {total_conflicts}")
    if total_conflicts:
        print("By severity:")
        for sev in ["Major", "Moderate", "Minor"]:
            print(f"  - {sev}: {by_sev.get(sev, 0)}")
        print(f"\nReport saved to: {out_csv}")
    else:
        print("✅ No conflicts found! (Safe prescriptions)")


if __name__ == "__main__":
    main()
