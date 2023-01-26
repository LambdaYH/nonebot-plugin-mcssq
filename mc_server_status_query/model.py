import sqlite3
from typing import Optional


class ServerDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_table()

    def _create_table(self):
        try:
            self._connect().execute(
                """CREATE TABLE IF NOT EXISTS McServerDBGroup
                          (id        INTEGER          ,
                           name      TEXT             ,
                           host      TEXT     NOT NULL,
                           port      INTEGER          ,
                           sv_type   TEXT     NOT NULL);"""
            )
            self._connect().execute(
                """CREATE TABLE IF NOT EXISTS McServerDBPrivate
                          (id        INTEGER          ,
                           name      TEXT             ,
                           host      TEXT     NOT NULL,
                           port      INTEGER          ,
                           sv_type   TEXT     NOT NULL);"""
            )
        except Exception as e:
            raise Exception(f"创建表发生错误: {e}")

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def add_server(
        self,
        group_id: int,
        user_id: int,
        name: str,
        host: str,
        port: Optional[int],
        sv_type: str,
    ):
        """
        添加服务器
        """
        conn = self._connect()
        conn.execute(
            f"INSERT INTO McServerDB{'Group' if group_id else 'Private'} (id, name, host, port, sv_type) \
                            VALUES (?,?,?,?,?)",
            (group_id if group_id else user_id, name, host, port, sv_type),
        )
        conn.commit()

    def del_server(self, group_id: Optional[int], user_id: Optional[int], name: str):
        """
        删除服务器
        """
        conn = self._connect()
        conn.execute(
            f"DELETE FROM McServerDB{'Group' if group_id else 'Private'} WHERE id=? AND name=?",
            (group_id if group_id else user_id, name),
        )
        conn.commit()

    def get_server(self, group_id: Optional[int], user_id: Optional[int], name: str):
        """
        获取以name命名的服务器
        """
        return (
            self._connect()
            .execute(
                f"SELECT host, port, sv_type FROM McServerDB{'Group' if group_id else 'Private'} WHERE id=? AND name=?",
                (group_id if group_id else user_id, name),
            )
            .fetchone()
        )

    def get_server_list(self, group_id: Optional[int], user_id: Optional[int]):
        """
        获取服务器列表
        返回name host port sv_type
        """
        return (
            self._connect()
            .execute(
                f"SELECT name, host, port, sv_type FROM McServerDB{'Group' if group_id else 'Private'} WHERE id=?",
                (group_id if group_id else user_id,),
            )
            .fetchall()
        )
