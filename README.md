# Upload client for the CREMA web-service (https://crema.unibas.ch)

This is a python script which uploads your files to the CREMA
web-server and starts the CREMA analysis.

All you need to do is to download **crema_uploader.py** script and start using it.

**Important!** This script requires Python3 as well as the *requests* library.

## Purpose

This script is aimed to users who has their data files stored on remote machines (usually linux) which can use this script to upload their data without use of an internet browser. So you do not need to copy files to your local machine for uploading to the CREMA server.

This is beta version to see if there are people interested in such application, We hope to get user feedback to properly shape the further development.

**All feedback is welcome!**

## Usage

```shell
python crema_uploader.py [-h] [-e EMAIL] [-p PROJECT]
                         [-t {chip-seq,atac-seq}]
                         [-o {hg19,mm10,rn6}]
                         --file-list TSV_FILE
```

### Optional arguments:

* -h, --help :  show this help message and exit
* -e EMAIL |: email address
* -p PROJECT : project name
* -t : data type {chip-seq, atac-seq}, default: chip-seq
* -o : organism ID, use hg19 for human, mm10 for mouse and rn6 for rat
* --file-list : TSV file list of files, ascii text, one line per file path

#### File format support
The following file formats are supported:
* **ATAC-Seq/ChIP-Seq** : .fastq[.gz]

#### TSV file format
The .tsv file contains paths to fastq files for uploading and annotation of these files i.e. to which condition and which type each file belongs to. All values in the tsv file are separated with tabs. Header line is required.
Here is an example:
```
sample	type	fq1	fq2
condition1	fg	/data/file1.fastq.gz
condition1	bg	/data/file2.fastq.gz
condition2	fg      /data/file3_R1.fastq.gz	/data/file3_R2.fastq.gz
condition2      bg	/data/file4_R1.fastq.gz	/data/file4_R2.fastq.gz
condition3	fg	/data/file5.fastq.gz
condition3	fg	/data/file6.fastq.gz
condition3	fg	/data/file7.fastq.gz
condition3	bg	/data/file8.fastq.gz
condition3	bg	/data/file9.fastq.gz
```

First column contains condition name for every fastq file (fastq pair). Second column contains type of a file either **fg** for foreground samples or **bg** for background samples. Third column contains path to fastq file or path fastq file for firs end reads in a pair. Fourth column contains path to the second end read file if data is paired end.
If you have data with multiple replicates per condition you can specify multiple fastq files per condition like in the example above for *condition3*. Your dataset could be a mixture of single-end and paired end fastq files. 

### Example

We run the script in background:
```shell
python crema_uploader.py -e user@example.com -p "my cool project" -data-type chip-seq -o hg19 \
    --file-list file_list.txt 1>crema_uploader.out 2>crema_uploader.err &
```

In the file crema_uploader.out the last lines contain a link to status page of your submission. If you submitted your email address then you will get a notification once your job is finished.
