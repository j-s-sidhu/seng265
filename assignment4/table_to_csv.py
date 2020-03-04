import csv
import re
import sys

def main():

    html = sys.stdin.read()

    #print(html)

    html = html.replace("\n", " ")
    sys.stdout.newline = ''

    #find all tables in the html file
    tables = re.findall('<table.*?>(.*?)</table.*?>', html, re.IGNORECASE)


    #go through each table and build proper output
    for x in range(0, len(tables)):
        if x > 0:
            print()
        sys.stdout.write("TABLE " + str(x+1) + ":\n")

        #current table
        table = (tables[x])

        table_headers = re.findall('<th.*?>(.*?)</th.*?>', table, re.IGNORECASE)

        #have a dictwriter if there are headers otherwise just write each row as it comes
        if table_headers:
            output = csv.DictWriter(sys.stdout,  fieldnames=table_headers, lineterminator='\n')
            output.writeheader()
        else:
            output = csv.writer(sys.stdout, lineterminator='\n')

        rows = re.findall('<tr.*?>(.*?)</tr.*?>', table, re.IGNORECASE)
        if table_headers:
            output_table(rows,  output, table_headers,)
        else:
            output_table(rows, output)

def output_table(rows, writer,headers=None):

    output_list = list()

    columns = 0
    if(headers == None):
        for y in range(0, len(rows)):
            #find all row data within the current row
            row_data = re.findall('<td.*?>(.*?)</td.*?>', rows[y], re.IGNORECASE)
            for st in row_data:
                tmp = re.sub("\s+", " ", st)
                row_data[row_data.index(st)] = tmp.strip()


            output_list.append(row_data)
            if len(row_data) > columns:
                columns = len(row_data)

        for row in output_list:
            #add as many empty entries as is needed to maintain column size requirement
            if len(row) < columns:
                while len(row) < columns:
                    row.append("")
            writer.writerow(row)


        return
    for y in range(1, len(rows)):
        row_data = re.findall('<td.*?>(.*?)</td.*?>', rows[y], re.IGNORECASE)


        row_dict = dict()
        for i in range(0, len(row_data)):
            #replace one or more whitespaces with a single space and then strip any leading or trailing whitespaces
            tmp = re.sub("\s+", " ", row_data[i])
            row_dict[headers[i]] = tmp.strip()
        writer.writerow(row_dict)


if __name__ == '__main__':
    main()
