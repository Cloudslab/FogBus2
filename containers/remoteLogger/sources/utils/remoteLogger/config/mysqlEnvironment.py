from dotenv import dotenv_values

mysqlEnv = dotenv_values(".mysql.env")


class MySQLEnvironment:
    user: str = mysqlEnv['USER']
    host: str = mysqlEnv['HOST']
    port: int = int(mysqlEnv['PORT'])
    password: str = mysqlEnv['PASSWORD']
