#!/usr/bin/env python3
"""
Run the research pipeline.

This script orchestrates the complete research workflow:
1. Load the 100-app list from the dataset
2. Research each app (extract, classify, score confidence)
3. Generate first-pass research output
4. Create verification sample for human review
5. Display research statistics

Usage:
    python scripts/run_research.py              # Full 100 apps
    python scripts/run_research.py --limit 10   # Test with 10 apps
    python scripts/run_research.py --help       # Show help
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

# Now import from src package
from config import (
    FIRST_PASS_RESEARCH_PATH,
    VERIFICATION_SAMPLE_PATH,
    VERIFICATION_SAMPLE_SIZE,
    APPS_PER_CATEGORY_IN_SAMPLE,
    save_research_output,
)
from research_agent import ResearchAgent
from research.verification import create_verification_sample

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run the AI research pipeline for 100 SaaS apps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_research.py              # Research all 100 apps
  python scripts/run_research.py --limit 10   # Test with 10 apps
  python scripts/run_research.py --quiet      # Suppress logging
        """,
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of apps to research (for testing)",
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress logging output",
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default=FIRST_PASS_RESEARCH_PATH,
        help="Output path for research results",
    )
    
    parser.add_argument(
        "--sample-only",
        action="store_true",
        help="Only create verification sample, don't run research",
    )
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    logger.info("=" * 70)
    logger.info("100-APP AI RESEARCH AGENT")
    logger.info("=" * 70)
    
    try:
        # Initialize agent
        agent = ResearchAgent(output_path=args.output)
        
        if args.sample_only:
            # Only create verification sample
            logger.info("Creating verification sample...")
            agent.load_apps()
            sample = create_verification_sample(
                agent.apps,
                sample_size=VERIFICATION_SAMPLE_SIZE,
                apps_per_category=APPS_PER_CATEGORY_IN_SAMPLE,
            )
            
            sample_output = {
                "metadata": {
                    "total_in_sample": len(sample),
                    "total_apps_in_dataset": len(agent.apps),
                    "apps_per_category": APPS_PER_CATEGORY_IN_SAMPLE,
                    "description": "Representative sample for human verification",
                },
                "apps": sample,
            }
            
            save_research_output(sample_output, VERIFICATION_SAMPLE_PATH)
            logger.info(f"Verification sample created: {len(sample)} apps")
            logger.info(f"Saved to: {VERIFICATION_SAMPLE_PATH}")
            return 0
        
        # Run full research pipeline
        logger.info("Starting research pipeline...")
        logger.info(f"Target: {'All apps' if args.limit is None else f'{args.limit} apps (test mode)'}")
        
        results = agent.run(limit=args.limit)
        
        logger.info(f"\n{'=' * 70}")
        logger.info("RESEARCH COMPLETE")
        logger.info(f"{'=' * 70}")
        
        # Generate and display statistics
        stats = agent.generate_stats()
        
        logger.info("\nResearch Statistics:")
        logger.info(f"  Total apps researched: {stats.get('total_apps', 0)}")
        logger.info(f"  Buildability:")
        for buildability, count in stats.get("buildability", {}).items():
            pct = (count / stats.get("total_apps", 1)) * 100
            logger.info(f"    - {buildability}: {count} ({pct:.1f}%)")
        logger.info(f"  Confidence:")
        for confidence, count in stats.get("confidence", {}).items():
            pct = (count / stats.get("total_apps", 1)) * 100
            logger.info(f"    - {confidence}: {count} ({pct:.1f}%)")
        logger.info(f"  MCP Available: {stats.get('mcp_available', 0)}")
        logger.info(f"  Self-serve: {stats.get('self_serve_apps', 0)}")
        
        # Save results
        agent.save_results()
        logger.info(f"Results saved to: {agent.output_path}")
        
        # Create verification sample
        logger.info("\nCreating verification sample...")
        sample = create_verification_sample(
            agent.research_results,
            sample_size=VERIFICATION_SAMPLE_SIZE,
            apps_per_category=APPS_PER_CATEGORY_IN_SAMPLE,
        )
        
        sample_output = {
            "metadata": {
                "total_in_sample": len(sample),
                "total_apps_in_dataset": stats.get("total_apps", 0),
                "apps_per_category": APPS_PER_CATEGORY_IN_SAMPLE,
                "description": "Representative sample for human verification",
            },
            "apps": sample,
        }
        
        save_research_output(sample_output, VERIFICATION_SAMPLE_PATH)
        logger.info(f"Verification sample created: {len(sample)} apps")
        logger.info(f"Saved to: {VERIFICATION_SAMPLE_PATH}")
        
        logger.info("\n" + "=" * 70)
        logger.info("NEXT STEPS:")
        logger.info("=" * 70)
        logger.info("1. Review first-pass research: " + str(FIRST_PASS_RESEARCH_PATH))
        logger.info("2. Verify sample apps: " + str(VERIFICATION_SAMPLE_PATH))
        logger.info("3. Run: python scripts/verify_sample.py")
        logger.info("=" * 70 + "\n")
        
        return 0
    
    except Exception as e:
        logger.error(f"Research pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
