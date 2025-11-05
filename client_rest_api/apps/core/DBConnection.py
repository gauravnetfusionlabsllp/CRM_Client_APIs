from django.db import connections

class DBConnection:
    
    @classmethod
    def _forFetchingData(cls, sqlQuery, using='default'): 
        data = []
        try:
            with connections[using].cursor() as cursor:
                cursor.execute(sqlQuery)
                data = cursor.fetchall()
        except Exception as e:
            print(sqlQuery)
            print(f"[Error] in (DBConnection._forFetchingData) msg: {str(e)}")
        return data

    @classmethod
    def _forInsertingData(cls, sqlQuery, using='default'):
        try:
            with connections[using].cursor() as cursor:
                cursor.execute(sqlQuery)
        except Exception as e:
            print(sqlQuery)
            print(f"[Error] in (DBConnection._forInsertingData) msg: {str(e)}")

    @classmethod
    def _forInsertingMultipleData(cls, sqlQuery, using='default'):
        try:
            with connections[using].cursor() as cursor:
                cursor.executemany(sqlQuery)
        except Exception as e:
            print(sqlQuery)
            print(f"[Error] in (DBConnection._forInsertingMultipleData) msg: {str(e)}")

    @classmethod
    def _forFetchingJson(cls, query, one=False, using='default'):
        try:
            with connections[using].cursor() as cursor:
                cursor.execute(query)
                columns = [col[0].lower() for col in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return data
        except Exception as e:
            print(query)
            print(f"[Error] in (DBConnection._forFetchingJson) msg: {str(e)}")
