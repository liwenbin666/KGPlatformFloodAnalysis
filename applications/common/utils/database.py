import pymysql
from pymysql import cursors
from flask import current_app


class DBUtils:
    def __init__(self):

        # self.db_host = 'localhost'
        # self.db_port = 3306
        # self.db_username = 'root'
        # self.db_password = '111111'
        # self.db_name = 'flood_analysis'

        self.db_host = '10.196.83.122'
        self.db_port = 3306
        self.db_username = 'root'
        self.db_password = 'bamboo1216'
        self.db_name = 'flood_analysis'

        try:
            # 连接数据库
            self.conn = pymysql.connect(host=self.db_host,
                                        port=self.db_port,
                                        user=self.db_username,
                                        password=self.db_password,
                                        db=self.db_name,
                                        charset='utf8mb4',
                                        cursorclass=cursors.DictCursor
                                        )
            # 获得cursor
            self.cursor = self.conn.cursor()

        except pymysql.MySQLError as e:
            print("MySQL 数据库连接存在问题: ", e)
        except BaseException as e1:
            print("其他异常:", e1)

    # def __del__(self):
    #     # 对象删除时触发
    #     if hasattr(self, 'cursor') and self.cursor:
    #         self.cursor.close()
    #     if hasattr(self, 'conn') and self.conn:
    #         self.conn.close()
    # def __del__(self):
    #     try:
    #         if hasattr(self, 'cursor') and self.cursor:
    #             self.cursor.close()
    #         if hasattr(self, 'conn') and self.conn:
    #             if not self.conn.closed:  # 检查连接是否已经关闭
    #                 self.conn.close()
    #     except Exception as e:
    #         print(f"Exception ignored in __del__: {e}")
    def __del__(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
        except Exception as e:
            print(f"Exception ignored in __del__: {e}")

    # def query(self, sql, params=None):
    #     try:
    #         self.cursor.execute(sql, params)
    #         return self.cursor.fetchall()
    #     except pymysql.MySQLError as e:
    #         print("MySQL 数据库查询存在问题: ", e)
    #     except BaseException as e1:
    #         print("其他异常:", e1)

    def query(self, sql, params=None):
        try:
            self.cursor.execute(sql, params)
            result = self.cursor.fetchall()
            if result:
                return result
            else:
                return None
        except pymysql.MySQLError as e:
            print("MySQL 数据库查询存在问题: ", e)
            return None
        except Exception as e:
            print("其他异常:", e)
            return None

    # def exec(self, sql, params=None):
    #     try:
    #         self.cursor.execute(sql, params)
    #         self.conn.commit()
    #     except pymysql.MySQLError as e:
    #         self.conn.rollback()
    #         print("MySQL 数据库执行存在问题: ", e)
    #     except BaseException as e1:
    #         print("其他异常:", e1)
    def exec(self, sql, params=None):
        try:
            # print(f"Executing SQL: {sql} with params: {params}")  # 添加调试信息
            self.cursor.execute(sql, params)
            self.conn.commit()
            return self.cursor.lastrowid
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print("MySQL 数据库执行存在问题: ", e)
            return None
        except BaseException as e1:
            print("其他异常:", e1)
            return None

    # def insert_and_get_id(self, sql, params=None):
    #     try:
    #         self.cursor.execute(sql, params)
    #         self.conn.commit()
    #         return self.cursor.lastrowid
    #     except pymysql.MySQLError as e:
    #         self.conn.rollback()
    #         print("MySQL 数据库执行存在问题: ", e)
    #     except BaseException as e1:
    #         self.conn.rollback()
    #         print("其他异常:", e1)
    #     return None

    def insert_and_getId(self, sql, data):
        if not self.cursor:
            print("Cursor 未初始化，无法执行 SQL 语句。")
            return None

        try:
            self.cursor.execute(sql, data)
            self.conn.commit()
            return self.cursor.lastrowid
        except pymysql.MySQLError as e:
            self.conn.rollback()
            print("MySQL 数据库插入存在问题: ", e)
        except BaseException as e1:
            self.conn.rollback()
            print("其他异常:", e1)
        return None

    def test_conn(self):
        res = self.query("SELECT DATABASE() AS db, USER() AS user")
        return {
            "mysql": res,
            "host": self.db_host,
            "pwd": self.db_password,
            "usr": self.db_username
        }

    def add_2_trans(self, sql, params=None):
        try:
            self.cursor.execute(sql, params)
        except pymysql.MySQLError as e:
            print("MySQL 数据库执行存在问题: ", e)
        except BaseException as e1:
            print("其他异常:", e1)

    def commit_cur_trans(self):
        try:
            self.conn.commit()
        except pymysql.MySQLError as e:
            # 失败则回滚
            self.conn.rollback()
            print("MySQL 数据库执行存在问题: ", e)
        except BaseException as e1:
            self.conn.rollback()
            print("其他异常:", e1)
