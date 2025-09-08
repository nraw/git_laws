import argparse
import os
import re
from pathlib import Path

import bson
import pandas as pd
from bs4 import BeautifulSoup as bs
from git import Repo
from loguru import logger
from markdownify import markdownify
from tqdm import tqdm


def main(law_id=None, output_dir=None):
    # https://podatki.gov.si/dataset/osnovni-podatki-o-predpisih-rs
    vpliva_na = pd.read_csv("data/vplivana.csv")
    osnovni_raw = pd.read_csv("data/osnovni.csv")
    osnovni = osnovni_raw.dropna(subset=["D_SPREJEMA"]).copy()
    osnovni["date_accepted"] = pd.to_datetime(osnovni["D_SPREJEMA"], format="%d.%m.%y")
    # https://podatki.gov.si/dataset/neuradna-preciscena-besedila-predpisov
    with open("data/vsebina.bson/pisrs/vsebina.bson", "rb") as f:
        laws = bson.decode_all(f.read())

    laws_list = [law["idPredpisa"] for law in laws]
    laws_changes = [law["idPredpisaChng"] for law in laws]

    if law_id is None:
        law_id = "ZAKO4697"
    law_code = get_law_code(law_id, osnovni)
    affected_ids = vpliva_na[vpliva_na.VPLIVA_NA == law_id]
    affected = osnovni[
        ((osnovni.ID.isin(affected_ids.ID)) & (osnovni.KRATICA.str.contains(law_code)))
        | (osnovni.ID == law_id)
    ]
    affected_laws = affected[affected.ID.str.startswith("ZAKO")].sort_values(
        "date_accepted"
    )

    if output_dir is None:
        data_location = "/tmp/slovenian_laws/"
    else:
        data_location = output_dir
    Path(data_location).mkdir(parents=True, exist_ok=True)
    repo = Repo.init(data_location)
    for _, affected_law_row in tqdm(affected_laws.iterrows()):
        #  affected_law_id = affected_laws["ID"].iloc[0]
        affected_law_id = affected_law_row["ID"]
        affected_law_title = affected_law_row["NASLOV"]
        affected_law_code = affected_law_row["KRATICA"]
        commit_msg = (
            affected_law_code + " - " + affected_law_id + " - " + affected_law_title
        )
        affected_law_date = affected_law_row["date_accepted"]
        affected_law = get_law(affected_law_id, laws)
        if not affected_law:
            continue
        vsebina = affected_law["vsebina"]
        vsebina_clean = re.sub(r"( |\n|\r)+", " ", vsebina)

        soup = bs(vsebina_clean)  # make BeautifulSoup
        prettyHTML = soup.prettify()
        #  vsebina_md = markdownify(vsebina, convert=["style"])
        #  vsebina_md = re.sub(
        #      "/(<!--.*?-->)|(<!--[\S\s]+?-->)|(<!--[\S\s]*?$)/g", "", vsebina_md
        #  )
        #  Path(data_location + law_code + ".md").write_text(vsebina_md)
        Path(data_location + law_code + ".html").write_text(prettyHTML)
        repo.git.add(all=True)
        repo.git.commit(date=affected_law_date, m=commit_msg)


def get_law(affected_law_id, laws):
    laws_list = [law["idPredpisa"] for law in laws]
    if affected_law_id in laws_list:
        law_number = laws_list.index(affected_law_id)
        law = laws[law_number]
    else:
        logger.warning(f"No law available for {affected_law_id}")
        law = ""
    return law


def get_law_code(law_id, osnovni):
    law_code = osnovni[osnovni.ID == law_id].iloc[0].KRATICA
    return law_code


def get_law_id(law_code, osnovni):
    law_id = osnovni[osnovni.KRATICA == law_code].iloc[0].ID
    return law_id


def get_markdown(vsebina):
    vsebina_md = markdownify(vsebina)
    return vsebina_md


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert Slovenian legal documents into git repositories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --law-id ZAKO4697 --output-dir ./repos/tax-law
  %(prog)s --law-id ZAKO1234 --output-dir /tmp/my-law-repo
  %(prog)s  # Uses defaults (ZAKO4697, /tmp/slovenian_laws/)
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
        default="/tmp/slovenian_laws/",
        help="Output directory for the git repository (default: /tmp/slovenian_laws/)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(law_id=args.law_id, output_dir=args.output_dir)
