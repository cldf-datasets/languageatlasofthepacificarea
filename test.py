
def test_valid(cldf_dataset, cldf_logger, cldf_sqlite_database):
    assert cldf_dataset.validate(log=cldf_logger)

    """
    select l.cldf_name, group_concat(o.cldf_name) from languagetable as l join `LanguageTable_languoids_in_source.csv` as oassoc on oassoc.languagetable_cldf_id = l.cldf_id join `languoids_in_source.csv` as o on o.cldf_id = oassoc.`languoids_in_source.csv_ID` group by l.cldf_id having count(o.cldf_id) > 1;
    """