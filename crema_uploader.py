""" Uploads files to CREMA webserver """

import argparse
import json
import logging
import os
import re
import requests
import time
import shutil
import sys
import tempfile

UPLOAD_URL = "https://crema.unibas.ch/crumara/upload"
RUN_URL = "https://crema.unibas.ch/crumara/run"

def main():
    parser = argparse.ArgumentParser(
        description='Uploads files to CREMA webserver.')
    parser.add_argument('-e',
                        help='email address',
                        dest='email',
                        default='')
    parser.add_argument('-p',
                        help='project name',
                        dest='project',
                        default='')
    parser.add_argument('--data-type', '-t',
                        help='data type',
                        dest='data_type',
                        choices=["chip-seq", "atac-seq"],
                        default='chip-seq')
    parser.add_argument('-o',
                        help='Organism id: hg19 for human, mm10 for mouse, rb6 for rat',
                        dest='organism',
                        choices=['hg19', 'mm10', 'rn6'],
                        default='hg19')

    parser.add_argument('--file-list',
                        help="TSV_FILE containing information on sample, sample type and file path",
                        dest="file_list",
                        required=True)

    args = parser.parse_args()

    upload_session = requests.Session()
    upload_session.verify = True
    upload_session.timeout = (10, 600)
    save_dir = get_sd(upload_session)

    # save user parameters
    job_data = {"email": args.email,
                "project": args.project,
                "organism": args.organism,
                "datatype": args.data_type,
                "submission": "uploader"}

    # save job parameters in advance
    try:
        r =  upload_session.post("https://crema.scicore.unibas.ch/crumara/save_json",
                                 data={"sd": save_dir,
                                       "data":json.dumps(job_data)})
        logging.warning("Job information is sent to the server.")
    except:
        logging.warning("Error: Could not save user parameters!\n%s!", str(sys.exc_info()))

    files = set()
    new_content = []
    with open(args.file_list) as fin:
        # read header
        content = [line.strip().split("\t") for line in fin if line.strip() != '']
        f1_idx = content[0].index("fq1")
        if "fq2" in content[0]:
            f2_idx = content[0].index("fq2")
        else:
            f2_idx = None
        new_content.append("\t".join(content[0]))
        for data in content[1:]:
            if len(data) < (f1_idx + 1):
                raise BaseException("\n->\t%s\nThis line does not have enough values. Please check the file formating." % "\t".join(data))
            filepath = data[f1_idx].strip()
            if is_link(filepath):
                data[f1_idx] = filepath
            else:
                files.add(filepath)
                filename = os.path.split(filepath)[1]
                data[f1_idx] = filename
                
            if f2_idx is not None and len(data) > f2_idx:
                filepath = data[f2_idx].strip()
                if is_link(filepath):
                    data[f2_idx] = filepath
                elif filepath != "":
                    files.add(filepath)
                    filename = os.path.split(filepath)[1]
                    data[f2_idx] = filename
            new_content.append("\t".join(data))

    #  make temp dir to keep modified samples.tsv for sending to server
    temp_dir = tempfile.mkdtemp(prefix=".crema_", dir="./")
    with open("%s/samples.tsv" % temp_dir, "wt") as fout:
        fout.write("\n".join(new_content))
    files.add("%s/samples.tsv" % temp_dir)

    for f in files:
        logging.warning("uploading file %s", f)
        with open(f, 'rb') as fin:
            index=0
            headers={}
            content_size = os.path.getsize(f)
            file_name = os.path.basename(f)
            for chunk in read_in_chunks(fin):
                offset = index + len(chunk)
                headers['Content-Type'] = 'application/octet-stream'
                headers['Content-length'] = str(content_size)
                headers['Content-Range'] = 'bytes %s-%s/%s' % (index, offset, content_size)
                index = offset
                error = ''
                for i in range(10):
                    try:
                        r =  upload_session.post(UPLOAD_URL, files={"files[]":(file_name, chunk)},
                                                 data={"sd": save_dir})
                        error = ''
                        break
                    except:
                        error = sys.exc_info()[0]
                        logging.warning("Error: %s!!!\nRetrying to re-upload data. Retry %d", str(sys.exc_info()), i+1)
                        time.sleep(60)
                if error != '':
                    logging.warning("Could not upload the data! Please report this id to CREMA administrators: %s!", save_dir)
        logging.warning("Finished uploading file %s", f)

    # remove temp dir after upload
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    # init job run after upload
    email = args.email
    project = args.project
    organism = args.organism
    data_type = args.data_type
    r = upload_session.post(RUN_URL, data={"sd": save_dir,
                                           "email": email,
                                           "project": project,
                                           "method": "crema_uploader",
                                           "datatype": data_type,
                                           "organism": organism})
    print("\n>>>>>>>>>>\nHere is link to your results:\n    %s" % (r.text.strip()))


def get_sd(mysession):
    """ get name of working directory for a project """
    url = "https://crema.scicore.unibas.ch/crumara/get_sd"
    res = mysession.get(url)
    res = [x for x in res.iter_lines()][0].decode("utf-8")
    return(res)


def read_in_chunks(file_object, chunk_size=50000000):
    """ Read file in chuncks """
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


def is_link(filepath):
    if re.match(r'^(http://|https://|ftp://)', filepath.strip()):
        return(True)
    if re.match(r'^SRR\d+$', filepath.strip()):
        return(True)
    return(False)
        

if __name__ == "__main__":
    main()
