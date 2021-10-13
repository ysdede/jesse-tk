

def run():
    print('Replace csv delimiters')
    import glob
    import csv
    from jessetk import utils

    csv_folder = 'jessepickerdata\\results\\top50'
    glob_filter = csv_folder + '/*.csv'

    print('Looking for files in:', csv_folder)
    dirList = glob.glob(glob_filter, recursive=False)
    print(f'Found {len(dirList)} csv files...')

    if dirList:
        for csv_fn in dirList:
            print('File name:', csv_fn)

            body = utils.read_file(csv_fn)
            body = body.replace("_W6,U", "_W6?U").replace(",VWWv", "?VWWv").replace("o4,@X", "o4?@X")


            utils.write_file(csv_fn, body)
    else:
        print('done...')


    # import csv
    #
    # with open('testfile.csv', newline='') as csvfile:
    #     data = list(csv.reader(csvfile))
    #
    # print(data)
