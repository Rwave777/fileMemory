import sqlite3


def insert_file_joined(cursor: sqlite3.Cursor, file_id: int, tag: str, number_of: int):
    """タグ登録と紐づけ登録

    Args:
        cursor (sqlite3.Cursor): _description_
        file_id (int): _description_
        tag (str): _description_
    """
    tag_id = 0
    cursor.execute(
        "SELECT id FROM tag_mng WHERE tag_name = ?",
        (tag,),
    )
    # 既存レコードがない場合のみ挿入
    result = cursor.fetchone()
    if not result:
        cursor.execute(
            "INSERT INTO tag_mng (tag_name) VALUES (?)",
            (tag,),
        )
        tag_id = cursor.lastrowid
    else:
        tag_id = result[0]
    cursor.execute(
        "INSERT OR IGNORE INTO file_tags (file_id, tag_id, number_of) VALUES (?,?,?)",
        (file_id, tag_id, number_of),
    )
