from dropbox import client, rest, session
import os
import sys

BASE_PATH = os.getcwd()
CHUNK_SIZE = 128 * 1024
APP_KEY = 'APP_KEY'
APP_SECRET = 'APP_SECRET'
ACCESS_TYPE = 'app_folder'


def init_session():
    sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
    request_token = sess.obtain_request_token()
    url = sess.build_authorize_url(request_token)

    print "Please visit this website and press the 'Allow' button, "
    print "then hit 'Enter' here:\n"
    print url
    raw_input()

    access_token = sess.obtain_access_token(request_token)

    c = client.DropboxClient(sess)
    print "linked account:", c.account_info()

    return c


def recursive_get_folder(client, folder):
    folder_metadata = client.metadata(folder)

    for c in folder_metadata["contents"]:
        if c["is_dir"]:
            dirname = BASE_PATH + c["path"]
            sys.stdout.write("Found directory %s ... " % dirname)
            sys.stdout.flush()

            if os.path.exists(dirname):
                sys.stdout.write("Exists local.\n")
            else:
                sys.stdout.write("Creating local...")
                sys.stdout.flush()
                os.makedirs(dirname)
                sys.stdout.write("Done.\n")

            sys.stdout.flush()

            previous_cwd = os.getcwd()
            os.chdir(dirname)
            recursive_get_folder(client, c["path"])
            os.chdir(previous_cwd)
        else:
            # Check if the file exists
            download = True
            local_filename = BASE_PATH + c["path"]
            sys.stdout.write("Checking %s ... " % c["path"])
            sys.stdout.flush()

            if os.path.exists(local_filename):
                sys.stdout.write("Exists ")
                sys.stdout.flush()
                # Compare if they are the same
                if os.path.getsize(local_filename) == c["bytes"]:

                # FIXME: Improve reliability
                #if os.path.getmtime(filename) == c.client_mtime:

                    sys.stdout.write("and are the same.\n")
                    sys.stdout.flush()
                    download = False
                else:
                    sys.stdout.write("but aren't the same. ")
            else:
                sys.stdout.write("Does not exist. ")
                sys.stdout.flush()

            if download:
                # Download the file
                sys.stdout.write("\nDownloading.. ")
                sys.stdout.flush()

                out = open(local_filename, "wb")
                f, metadata = client.get_file_and_metadata(c["path"])
                total_size = metadata["bytes"]
                written = 0
                while True:
                    data = f.read(CHUNK_SIZE)
                    if data == '':
                        break
                    else:
                        out.write(data)
                        written = written + len(data)

                    percent = written * 30 / total_size

                    #percent_line = "[" + ("*" * percent) +
                    #               (" " * (30 - percent)) +
                    #                "] " + str(written) + "/" +
                    #                str(total_size)
                    percent_line = "[%s%s] %d/%d" % (("*" * percent),
                                                     (" " * (30 - percent)),
                                                     written, total_size)

                    sys.stderr.write(percent_line)
                    sys.stderr.write("\b" * (len(percent_line)))
                    sys.stderr.flush()

                out.close()

                sys.stdout.write("Done. \n")

if __name__ == "__main__":
    client = init_session()

    recursive_get_folder(client, "/")
