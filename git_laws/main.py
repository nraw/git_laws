import argparse
import sys

from loguru import logger

from .law_converter import LawConverter


def main(law_id: str = None, output_dir: str = None) -> None:
    """
    Main function to process Slovenian legal documents into git repositories.

    Args:
        law_id: MOPED ID of the law to process (defaults to "ZAKO4697")
        output_dir: Output directory for git repository (defaults to "/tmp/slovenian_laws/")
    """
    # Set defaults
    if law_id is None:
        law_id = "ZAKO4697"

    if output_dir is None:
        output_dir = "/tmp/slovenian_laws/"

    logger.info(f"Starting git-laws processing for law {law_id}")

    # Initialize the law converter with dependency injection
    converter = LawConverter()

    # Convert the law using the new architecture
    try:
        success = converter.convert_law(law_id, output_dir)

        if success:
            logger.info(f"✓ Successfully converted law {law_id}")
            sys.exit(0)
        else:
            logger.error(f"✗ Failed to convert law {law_id}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error during conversion: {e}")
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert Slovenian legal documents into git repositories using PISRS API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --law-id ZAKO4697 --output-dir ./repos/tax-law
  %(prog)s --law-id ZAKO1234 --output-dir /tmp/my-law-repo
  %(prog)s  # Uses defaults (ZAKO4697, /tmp/slovenian_laws/)

Note: This tool now uses the PISRS API directly and downloads only the required
data for the specified law, making it much faster than previous bulk approaches.
        """
    )
    parser.add_argument(
        "--law-id",
        type=str,
        default="ZAKO4697",
        help="ID of the law to process (default: ZAKO4697)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for the git repository (default: /tmp/slovenian_laws/)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    try:
        args = parse_args()
        main(law_id=args.law_id, output_dir=args.output_dir)
            
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error("Please check your PISRS_API_KEY and network connectivity")
        sys.exit(1)
