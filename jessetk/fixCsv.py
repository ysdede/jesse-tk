def run():
    print('Replace csv delimiters')
    import glob
    from jessetk import utils

    csv_folder = 'jessepickerdata\\results\\top50'
    glob_filter = csv_folder + '/*.csv'

    print('Looking for files in:', csv_folder)
    dirList = glob.glob(glob_filter, recursive=False)
    print(f'Found {len(dirList)} csv files...')

    if dirList:
        for csv_fn in dirList:
            print('File name:', csv_fn)
            utils.write_file(csv_fn, utils.read_file(csv_fn).replace(",", "\t"))

