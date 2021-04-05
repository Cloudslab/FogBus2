if __name__ == '__main__':
    from mysql import connector

    conn = connector.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='passwordForRoot',
        database='FogBus2_Tasks')

    cursor = conn.cursor()
    import json

    f = open('dependencies.json', 'r')
    t = json.load(f)
    f.close()

    for task in t['tasks'].values():
        taskID = task['id']
        taskName = task['name']
        sql = 'INSERT INTO tasks' \
              ' (id,name) ' \
              'VALUES(%d,"%s") ' \
              'ON DUPLICATE KEY ' \
              'UPDATE name="%s"' \
              % (
                  taskID, taskName, taskName)
        cursor.execute(sql)
    conn.commit()

    # conn = connector.connect(
    #     host='127.0.0.1',
    #     port=3306,
    #     user='root',
    #     password='passwordForRoot',
    #     database='FogBus2_Applications'
    # )

    # cursor = conn.cursor()
    #
    # i = 0
    # for application in t['applications'].values():
    #     name = application['name']
    #     taskWithDependency = application['dependencies']
    #     taskWithDependency = json.dumps(taskWithDependency)
    #     sql = 'INSERT INTO applications' \
    #           ' (id,name,tasksWithDependency) ' \
    #           'VALUES(%d,\'%s\',\'%s\') ' \
    #           'ON DUPLICATE KEY ' \
    #           'UPDATE name=\'%s\',tasksWithDependency=\'%s\'' \
    #           % (
    #               i, name, taskWithDependency,
    #               name, taskWithDependency
    #           )
    #     print(sql)
    #     cursor.execute(sql)
    #     i += 1
    # conn.commit()
