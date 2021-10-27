def run():  # TODO Convert to Class and make it clear.
    import glob
    import csv
    from collections import Counter
    from jessetk import utils

    csv_folder = 'jessepickerdata\\results'  # TODO: Move to new data dir or make it optional.
    glob_filter = csv_folder + '/*.csv'

    print('Looking for files in:', csv_folder)
    dirList = glob.glob(glob_filter, recursive=False)
    print(f'Found {len(dirList)} csv files...')

    cnt = Counter()
    count = {}
    if dirList:
        for csv_fn in dirList:
            print('File name:', csv_fn)
            with open(csv_fn, newline='') as cf:
                body = utils.read_file(csv_fn)
                # body = body.replace("','", "\t")
                data = list(csv.reader(cf, delimiter=",", quotechar="'"))
                # data = list(csv.reader(cf, delimiter=","))
                for row in data[1:]:
                    # print(row[2], row[10], row[11])
                    cnt[row[2]] += float(row[11])

        sorted_list = sorted(cnt.items(), key=lambda x: x[1], reverse=True)
        sorted_list = sorted_list[0:20]

        for k in cnt:
            print(k, round(cnt[k], 2))

        print('*' * 50)
        print(sorted_list)
        print(type(sorted_list))

        for k, v in sorted_list:
            print('Dna and pairs: ', k, round(v, 2))

            for csv_fn in dirList:
                # print('File name:', csv_fn)
                with open(csv_fn, newline='') as cf:
                    body = utils.read_file(csv_fn)
                    # body = body.replace("','", "\t")
                    data = list(csv.reader(cf, delimiter=",", quotechar="'"))
                    # data = list(csv.reader(cf, delimiter=","))
                    for row in data[1:]:
                        # print(row[2], row[10], row[11])
                        if row[2] == k and float(row[11]) >2:
                            print(row)


    else:
        print('done...')
