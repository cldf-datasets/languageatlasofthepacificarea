
def test_valid(cldf_dataset, cldf_logger, cldf_sqlite_database):
    assert cldf_dataset.validate(log=cldf_logger)

    res = cldf_sqlite_database.query(
        'select l.cldf_name, count(c.cldf_id) as c, group_concat(c.cldf_name) '
        'from languagetable as l '
        'join LanguageTable_ContributionTable as oassoc on oassoc.languagetable_cldf_id = l.cldf_id '
        'join contributiontable as c on c.cldf_id = oassoc.contributiontable_cldf_id '
        'group by l.cldf_id having count(c.cldf_id) > 1 order by c desc limit 10;'
    )[0]
    assert res[0] == 'Austronesian' and res[1] >= 1259
