import os
from pathlib import Path

import bson
import pandas as pd
from git import Repo

data_location = "/tmp/slovenian_laws/"
os.mkdir(data_location)


def main():
    vpliva_na = pd.read_csv("data/vplivana.csv")
    osnovni_raw = pd.read_csv("data/osnovni.csv")
    osnovni = osnovni_raw.dropna(subset=["D_SPREJEMA"]).copy()
    osnovni["date_accepted"] = pd.to_datetime(osnovni["D_SPREJEMA"], format="%d.%m.%y")
    with open("data/vsebina.bson/pisrs/vsebina.bson", "rb") as f:
        laws = bson.decode_all(f.read())

    laws_list = [law["idPredpisa"] for law in laws]
    laws_changes = [law["idPredpisaChng"] for law in laws]
    laws_changes == law_id

    law_id = "ZAKO4697"
    law_code = osnovni[osnovni.ID == law_id].iloc[0].KRATICA
    affected_ids = vpliva_na[vpliva_na.VPLIVA_NA == law_id]
    affected = osnovni[
        ((osnovni.ID.isin(affected_ids.ID)) & (osnovni.KRATICA.str.contains(law_code)))
        | (osnovni.ID == law_id)
    ]
    affected_laws = affected[affected.ID.str.startswith("ZAKO")].sort_values(
        "date_accepted"
    )
    repo = Repo.init(data_location)
    for _, affected_law_row in affected_laws.iterrows():
        #  affected_law_id = affected_laws["ID"].iloc[0]
        affected_law_id = affected_law_row["ID"]
        affected_law_title = affected_law_row["NASLOV"]
        affected_law_code = affected_law_row["KRATICA"]
        commit_msg = (
            affected_law_code + " - " + affected_law_id + " - " + affected_law_title
        )
        affected_law_date = affected_law_row["date_accepted"]
        affected_law = get_law(affected_law_id, laws)
        Path(data_location + law_code + ".html").write_text(affected_law["vsebina"])
        repo.git.add(all=True)
        repo.git.commit(date=affected_law_date, m=commit_msg)


def get_law(law_id, laws):
    laws_list = [law["idPredpisa"] for law in laws]
    law_number = laws_list.index(law_id)
    law = laws[law_number]
    return law


if __name__ == "__main__":
    main()
