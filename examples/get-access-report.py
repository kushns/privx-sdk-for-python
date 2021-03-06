# Requires Python 3.6+
import sys
import csv
import getopt

# Import the PrivX python library.
import privx_api

# Import the configs.
import config

# Initialize the API.
api = privx_api.PrivXAPI(config.HOSTNAME, config.HOSTPORT, config.CA_CERT,
                         config.OAUTH_CLIENT_ID, config.OAUTH_CLIENT_SECRET)

# Authenticate.
# NOTE: fill in your credentials from secure storage, this is just an example
api.authenticate("API client ID", "API client secret")

def get_user_id(user):
    resp = api.search_users(keywords=user)
    if resp.ok():
        data_load = resp.data()
        data_items = data_load['items']
        user_id = False
        for user_data in data_items:
            if user_data['principal'] == user:
                user_id = user_data['id']
        if user_id:
            return user_id
        else:
            print(user+": User not found")
            sys.exit(2)
    else:
        error = "Get users operation failed:"
        process_error(error)

def get_connection_data(user_id):
    offset = 0
    limit = 1000
    if user_id:
        resp = api.search_connections(user_id=[user_id], offset=offset, limit=limit)
    else:
        resp = api.search_connections(offset=offset, limit=limit)

    if resp.ok():
        data_load = resp.data()
        data_items = data_load['items']
        count = data_load['count'] - limit
        while count > 0:
            offset = offset + limit
            if user_id:
                resp = api.search_connections(user_id=[user_id], offset=offset, limit=limit)
            else:
                resp = api.search_connections(offset=offset, limit=limit)
            data_load = resp.data()
            if resp.ok():
                data_items = data_items + data_load['items']
                count = count - limit
        connections_data = {}
        all_data = []
        data = ("type,mode,authentication_method,target_host_address,"
                "target_host_account,connected,disconnected")
        data_list = data.split(',')
        for connection_data in data_items:
            connections_data["user"] = connection_data['user']['display_name']
            for p in data_list:
                if p in ("connected", "disconnected"):
                    connection_data[p] = connection_data[p].split(".")[0]
                if p == "authentication_method":
                    connection_data[p] = ','.join(connection_data[p])
                connections_data[p] = connection_data[p]
            all_data.append(dict(connections_data))
        return all_data
    else:
        error = "Get users Connection data operation failed:"
        process_error(error)


def export_connection_data(user, user_id=None, header_printed=False):
    output_csvfile = user+"_connection_data.csv"
    with open(output_csvfile, "w") as f:
        connection_data = get_connection_data(user_id)
        print("Writing Connection data to", output_csvfile, end=' ')
        for data in connection_data:
            w = csv.DictWriter(f, data.keys())
            if not header_printed:
                w.writeheader()
                header_printed = True
            w.writerow(data)
    print("\nDone")


def usage():
    print("")
    print(sys.argv[0], " -h or --help")
    print(sys.argv[0], " -u user1")
    print(sys.argv[0], " --user ALL")


def process_error(messages):
    print(messages)
    sys.exit(2)


def main():
    user = "ALL"
    if (len(sys.argv) > 3):
        usage()
        sys.exit(2)
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hu:", ["help", "user="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-u", "--user"):
            user = arg
        else:
            usage()
    if user == "ALL":
        export_connection_data(user)
    else:
        user_id = get_user_id(user)
        export_connection_data(user, user_id)


if __name__ == '__main__':
    main()
