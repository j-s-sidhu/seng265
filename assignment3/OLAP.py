#!/usr/bin/env python3

import argparse
import os
import sys
import csv

class Custom_Action(argparse._StoreAction):
    def __call__(self, parser, namespace, values, option_string=None):
        temp = list()
        order = list()
        try:
            order = getattr(namespace, 'order')
        except:
            order = []


        temp = getattr(namespace, self.dest)
        if temp == None:
            temp = []

        temp.append(values)
        setattr(namespace, self.dest, temp)
        order.append(self.dest)
        setattr(namespace, 'order', order)

class Count_Action(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, True)

        order = list()
        try:
            order = getattr(namespace, 'order')
        except:
            order = []

        order.append(self.dest)
        setattr(namespace, 'order', order)

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--min', action=Custom_Action)
    parser.add_argument('--max',   action=Custom_Action)
    parser.add_argument('--mean',   action=Custom_Action)
    parser.add_argument('--sum',  action=Custom_Action)
    parser.add_argument('--count', nargs=0, action=Count_Action)
    parser.add_argument('--group-by')
    parser.add_argument('--input')
    parser.add_argument('--top', nargs=2, action=Custom_Action)

    parsed = parser.parse_args(sys.argv[1:])

    input_file = open(parsed.input, 'r')
    csv_read = csv.DictReader(input_file)
    agg_field_errors = dict()
    fields = csv_read.fieldnames
    agg_dict = dict()
    mean_dict = dict()
    mean_counter_dict = dict()
    sum_dict = dict()
    top_k_dict = dict() #holds the fields of which top k needs to be found
    top_k_unique = dict() # key will be top_<field> value will be a list of all unique values encountered
    count = 0

    #Now that input is confirmed valid move all required fields into a dictionary
    #Example key:value is min_Ticker:3
    #can store a running min and max this way
    #mean can be computed the same way by taking the (sum / (line_num - 1))
    # may actually be able to to do ^^ because of the error dict so just take (sum/ (line_num - 1 - # of invalid entries))
    # Done Above to save time checking for None fields

    #At this point all lists and dictionarys are set up as required and we can proceed to read the file line by line_num
    #Will probably be easier if there exist two cases one for group by specified and another for group by not specified
    if(parsed.group_by == None):

        if(parsed.min != None):
            validate(fields, parsed.min, parsed.input)
            add_to_dict(parsed.min, agg_dict,"min", agg_field_errors)
        if(parsed.max != None):
            validate(fields, parsed.max, parsed.input)
            add_to_dict(parsed.max, agg_dict, "max", agg_field_errors)
        if(parsed.mean != None):
            validate(fields, parsed.mean, parsed.input)
            add_to_dict(parsed.mean, agg_dict, "mean", agg_field_errors)
        if(parsed.sum != None):
            validate(fields, parsed.sum, parsed.input)
            add_to_dict(parsed.sum, agg_dict, "sum", agg_field_errors)
        if(parsed.top != None):

            #make the top k dict here because its probably easier than modifiying the function to build it
            #top_k_dict has key value of format "top_<field>" being the key and the value being a list with k values initialized to None

            for top_k_field in parsed.top:
                if top_k_field[1] not in fields:
                    sys.stderr.write("Error: " + parsed.input + ":no field with name \'" + top_k_field[1]+ "\'")
                    sys.exit(8)
                s = "top_"+top_k_field[1]
                top_k_dict[s] = dict()


        if(parsed.group_by != None):
            if parsed.group_by not in fields:
                sys.stderr.write("Error " + parsed.input + ": no group-by argument with name \'" + parsed.group_by + "\' found\n")
                sys.exit(9)

        for line in csv_read:
# line is a dictionary with field name being the key and value being whatever is in that field in the given row
# so go through each key
            aggregate_add(line, agg_field_errors, "min", agg_dict, parsed.input, csv_read.line_num)
            aggregate_add(line, agg_field_errors, "max", agg_dict, parsed.input, csv_read.line_num)
            aggregate_add(line, agg_field_errors, "mean", agg_dict, parsed.input, csv_read.line_num)
            aggregate_add(line, agg_field_errors, "sum", agg_dict, parsed.input, csv_read.line_num)

            # key will tell what key to check in "line"


            top_k_add(line, top_k_unique, top_k_dict, parsed.input, csv_read.line_num)

        #build top k dictionary
        for key in top_k_unique:
            field = key[key.index("_")+1:]
            if (top_k_unique[key] > 20):
                sys.stderr.write("Error: " + parsed.input + ": " + field + " has been capped at 20 distinct values")

        if parsed.top != None:
            for k_field in parsed.top:
                key = "top_" + k_field[1]
                num_list = list()
                for key2 in top_k_dict[key]:
                    x = top_k_dict[key][key2]
                    st = key2 +": " + str(x)
                    num_list.append(st)
                # sort in descedning order
                sorted(num_list, key=sort_help, reverse=True)
                top_k_dict[key] = num_list[0:int(k_field[0])]


        # Combine the top k values for each categorical field into one entry and put in agg_dict
        for key in top_k_dict:
            top_k_entry = ""
            for item in top_k_dict[key]:

                top_k_entry = top_k_entry + item + ","

            top_k_entry = top_k_entry[0:len(top_k_entry)]
            agg_dict[key]= top_k_entry


        count = csv_read.line_num - 1

        mean_keys = sorted(mean_dict.keys())
        actual_mean_dict = dict()

        output_fields = list()

        if hasattr(parsed, 'order'):
            for item in parsed.order:
                ind = sys.argv.index("--"+item)

                if item == "count":
                    output_fields.append("count")
                    agg_dict["count"] = count
                elif item == "top":
                    field = sys.argv[ind+2]
                    output_fields.append(item + "_" + field)
                    sys.argv.remove("--"+item)
                    sys.argv.remove(field)
                else:
                    field = sys.argv[ind+1]
                    output_fields.append(item + "_" + field)
                    sys.argv.remove("--"+item)
                    sys.argv.remove(field)

        if(len(output_fields) == 0):
            output_fields.append("count")
            agg_dict["count"] = count

        if(parsed.mean != None):
            for field in parsed.mean:
                total = int(agg_dict["mean_"+field])
                counter = int(agg_dict["mean_"+field+"_counter"])
                agg_dict["mean_"+field] = total/counter
                agg_dict.pop("mean_"+field+"_counter")

        csv_writer = csv.DictWriter(sys.stdout, fieldnames=output_fields)
        csv_writer.writeheader()
        csv_writer.writerow(agg_dict)
    # End of non-grouped by output
    else:



        group_list = list() #list to hold all the unique groups that are encountered up to whatever point we are at in the file
        count_dict = dict() # list to count number of records for each group value

        if parsed.group_by not in fields:
            sys.stderr.write("Error: "+parsed.input + ":no group-by argument with name \'" + parsed.group_by + "\'\n")
            sys.exit(9)

        add_to_dict_group(csv_read, agg_dict, agg_field_errors, parsed, parsed.group_by, group_list, count_dict)
        if len(group_list) > 20:
            sys.stderr.write("Error: " + parsed.input + ": " + parsed.group_by + " has been capped at 20 values\n")
            group_list = group_list[:20]
        #group list holds up to the first 20 distinct values for the grouping specified
        #so go through each group and build the base of the dicitonary
        for group in group_list:
            if parsed.min != None:
                for field in parsed.min:
                    if field not in fields:
                        sys.stderr.write("Error: " + parsed.input + ":no field with name \'" + field + "\'\n")
                        sys.exit(8)

                    key = group + "_min_" + field
                    agg_dict[key] = "NaN"
            if parsed.max != None:
                for field in parsed.max:
                    if field not in fields:
                        sys.stderr.write("Error: " + parsed.input + ":no field with name \'" + field + "\'\n")
                        sys.exit(8)

                    key = group + "_max_" + field
                    agg_dict[key] = "NaN"
            if parsed.mean != None:
                for field in parsed.mean:
                    if field not in fields:
                        sys.stderr.write("Error: " + parsed.input + ":no field with name \'" + field + "\'\n")
                        sys.exit(8)

                    key = group + "_mean_" + field
                    agg_dict[key] = "NaN"
                    agg_dict[key+"_counter"] = 0
            if parsed.sum != None:
                for field in parsed.sum:
                    if field not in fields:
                        sys.stderr.write("Error: " + parsed.input + ":no field with name \'" + field + "\'\n")
                        sys.exit(8)

                    key = group + "_sum_" + field
                    agg_dict[key] = "NaN"

            if(parsed.top != None):
                for top_k_field in parsed.top:
                    if top_k_field[1] not in fields:
                        sys.stderr.write("Error: " + parsed.input + ":no field with name \'" + top_k_field[1]+ "\'")
                        sys.exit(8)

                    s = group+"_top_"+top_k_field[1]
                    k_list = [None] * int(top_k_field[0])
                    top_k_dict[s] = dict()


        if len(group_list) > 20:
            if parsed.min != None:
                for thing in parsed.min:
                    agg_dict["OTHER_min_" + thing] = "NaN"
            if parsed.max != None:
                for thing in parsed.max:
                    agg_dict["OTHER_max_" + thing] = "NaN"
            if parsed.mean != None:
                for thing in parsed.mean:
                    agg_dict["OTHER_mean_" + thing] = "NaN"
            if parsed.sum != None:
                for thing in parsed.sum:
                    agg_dict["OTHER_sum_" + thing] = "NaN"


        input_file.close()

        input_file = open(parsed.input, 'r')
        csv_read = csv.DictReader(input_file)


        for line in csv_read:

            aggregate_add_group(line, agg_field_errors, "min", agg_dict, parsed.input, csv_read.line_num,group_list, parsed.group_by)
            aggregate_add_group(line, agg_field_errors, "max", agg_dict, parsed.input, csv_read.line_num,group_list, parsed.group_by)
            aggregate_add_group(line, agg_field_errors, "mean", agg_dict, parsed.input, csv_read.line_num,group_list, parsed.group_by)
            aggregate_add_group(line, agg_field_errors, "sum", agg_dict, parsed.input, csv_read.line_num,group_list, parsed.group_by)

            top_k_add_group(line, top_k_unique, top_k_dict, parsed.input, csv_read.line_num, group_list, parsed.group_by)

        #build top k dictionary
        if parsed.top != None:
            for group in group_list:
                for k_field in parsed.top:
                    key = group + "_top_" + k_field[1]
                    num_list = list()
                    for key2 in top_k_dict[key]:
                        x = top_k_dict[key][key2]
                        st = key2 +": " + str(x)
                        num_list.append(st)
                # sort in descedning order
                sorted(num_list, key=sort_help, reverse=True)
                top_k_dict[key] = num_list[0:int(k_field[0])]



        for key in top_k_dict:
            top_k_entry = ""
            for item in top_k_dict[key]:

                top_k_entry = top_k_entry + item + ","

            top_k_entry = top_k_entry[0:len(top_k_entry)]
            agg_dict[key]= top_k_entry



        output_fields = list()
        output_fields.append(parsed.group_by)

        #build the output fields in the correct order
        if hasattr(parsed, 'order'):
            for item in parsed.order:
                ind = sys.argv.index("--"+item)

                if item == "count":
                    output_fields.append("count")
                    agg_dict["count"] = count
                elif item == "top":
                    field = sys.argv[ind+2]
                    output_fields.append(item + "_" + field)
                    sys.argv.remove("--"+item)
                    sys.argv.remove(field)
                else:
                    field = sys.argv[ind+1]
                    output_fields.append(item + "_" + field)
                    sys.argv.remove("--"+item)
                    sys.argv.remove(field)

        if len(output_fields) == 1:
            output_fields.append("count")

        writer = csv.DictWriter(sys.stdout, fieldnames=output_fields)
        writer.writeheader()
        sorted(group_list)
        for value in group_list:
            row_dict = dict();
            row_dict[parsed.group_by] = value

            for field in output_fields[1:]:
                if field == "count":
                    row_dict["count"] = count_dict[value]

                elif field == "mean":
                    s = agg_dict[value+"_"+field]
                    c = agg_dict[value+"_"+field+"_counter"]
                    row_dict[field] = s/c
                else:
                    key = value + "_" + field
                    row_dict[field] = agg_dict[key]

            writer.writerow(row_dict)


#Takes string s of format 'amzn: 3049'
def sort_help(s1):
    ind1 = s1.index(":")
    number1 = int(s1[ind1+2:])
    return (number1)


#line dict is the line we are reading
#error dict is to hold unique values for a requested field
def top_k_add(line_dict, error_dict, top_k_dict, file_name, line):

    for field in line_dict:
        test_categ = "top_"+field



        # see if 20 distinct values have been found
        # if havent seen the test category yet then should set it to 0
        try:
            error_dict[test_categ] == 20

        except:
            error_dict[test_categ] = 0

        if test_categ in top_k_dict:
            try:
                top_k_dict[test_categ][line_dict[field]] = top_k_dict[test_categ][line_dict[field]] + 1

            except:
                if error_dict[test_categ] <= 20:
                    top_k_dict[test_categ][line_dict[field]] = 1
                    error_dict[test_categ] = error_dict[test_categ] + 1 # once error_dict[test_categ] become > 20 we have found 20 distinct values so give an error code and exit

def top_k_add_group(line_dict, error_dict, top_k_dict, file_name, line, group_list, group):

    for field in line_dict:
        test_categ = line_dict[group] + "_top_"+field

        if field not in error_dict:

            error_dict[field] = 0

        if test_categ in top_k_dict:
            try:
                top_k_dict[test_categ][line_dict[field]] = top_k_dict[test_categ][line_dict[field]] + 1

            except:
                if error_dict[field] <= 20:
                    top_k_dict[test_categ][line_dict[field]] = 1
                    error_dict[field] = error_dict[field] + 1 # once error_dict[test_categ] become > 20 we have found 20 distinct values so give an error code and exit


#line dict is the dictionary holding the values of the current line_num
# error dict is to see how many invalid values have been found for error messages
# aggregate is a string of the aggregate ex. "min"
#agg dict is the dictionary holding the current value for that argument ex. agg_dict[Open] could hold 3. meaning 3 is the smallest value up to this point
#file name is to help with error message
#line is also to help with error message
def aggregate_add(line_dict, error_dict, aggregate, agg_dict, file_name, line):

#False if value was invalid

    for field in line_dict:
        valid_arg = False
        test_agg = aggregate+"_"+field

        if test_agg in agg_dict:
            value = line_dict[field]
            try:
                value = float(value)
                valid_arg = True
            except:
                if(error_dict[field] > 100):
                    sys.stderr.write("Error: " + file_name + ":more than 100 non-numeric values found in aggregate column \'" + field + "\'\n")
                    sys.exit(7)
                else:
                    sys.stderr.write(file_name + ":" + str(line) + ":" + " can't compute " + aggregate + " on non-numeric value \'" + line_dict[field] +"\'\n")
                    error_dict[field] = error_dict[field]+1
                    valid_arg = False

            if(valid_arg == True):

                if (agg_dict[test_agg] == "NaN"):
                    agg_dict[test_agg] = value #the first value will always be the min, max, mean, and sum, so no need for a special cases

                else:
                    if(aggregate == "min"):
                        agg_dict[test_agg] = min(agg_dict[test_agg], value)
                    elif(aggregate == "max"):
                        agg_dict[test_agg] = max(agg_dict[test_agg], value)
                    elif(aggregate == "mean"):
                        value = value + agg_dict[test_agg]
                        agg_dict[test_agg] = value
                        test_agg = test_agg +"_counter"
                        agg_dict[test_agg] = agg_dict[test_agg]+1
                    elif(aggregate == "sum"):
                        agg_dict[test_agg] = agg_dict[test_agg] + value


#modified from aggregate_add
def aggregate_add_group(line_dict, error_dict, aggregate, agg_dict, file_name, line, group_list, group_name):

#False if value was invalid

    for field in line_dict:
        valid_arg = False
        # if the member of the group has not been ecnountered add it to the list of ones seen
        # test_agg is for example. ibm_min_Low
        test_agg = line_dict[group_name] + "_" +aggregate+"_"+field


        # if 20 values seen then disregard the unique part and just put on other is how i interpreted the assignment
        if test_agg not in agg_dict:
            test_agg = aggregate + "_" + field + "_OTHER"

        # if in the agg dict we have already seen it previously
        if test_agg in agg_dict:
            value = line_dict[field]
            try:
                value = float(value)
                valid_arg = True
            except:
                if(error_dict[test_agg] > 100):
                    sys.stderr.write("Error: " + file_name + ":more than 100 non-numeric values found in aggregate column \'" + field + "\'")
                    sys.exit(7)
                else:
                    sys.stderr.write(file_name + ":" + str(line) + ":" + " can't compute " + aggregate + " on non-numeric value \'" + line_dict[field] +"\'\n")
                    error_dict[field] = error_dict[field]+1
                    valid_arg = False

            if(valid_arg == True):

                if (agg_dict[test_agg] == "NaN"):
                    agg_dict[test_agg] = value #the first value will always be the min, max, mean, and sum, so no need for a special cases
                    if aggregate == "mean":
                        agg_dict[test_agg + "_counter"] = 1

                else:
                    if(aggregate == "min"):
                        agg_dict[test_agg] = min(agg_dict[test_agg], value)
                    elif(aggregate == "max"):
                        agg_dict[test_agg] = max(agg_dict[test_agg], value)
                    elif(aggregate == "mean"):
                        value = value + agg_dict[test_agg]
                        agg_dict[test_agg] = value
                        test_agg = test_agg +"_counter"
                        agg_dict[test_agg] = agg_dict[test_agg]+1
                    elif(aggregate == "sum"):
                        agg_dict[test_agg] = agg_dict[test_agg] + value

            # if test_agg is not in dict then this is the first time seeing this instance of the thing
            # that means that if it is a valid value it becomes the value of that aggregate by default and if it is not then that aggregate becomes NaN



#lst is list with the fields each field is added to dict and str is to indicated what operation is being performed
def add_to_dict(lst, dict, s, error_fields):

    for field in lst:
        key = s+"_"+field
        dict[key] = "NaN"
        error_fields[field] = 0

        #special case for mean to have a counter for each mean that we are required to compute so that at the end it can be easily calculated
        if(s == "mean"):
            key = key + "_counter"
            dict[key] = 0


def add_to_dict_group(csv_read, dict, error_fields, parsed, group, group_list, count_dict):

    for line in csv_read:

        for field in line:
            if field == group and len(group_list) <= 20:
                if line[field] not in count_dict:
                    count_dict[line[field]] = 1
                else:
                    count_dict[line[field]] = count_dict[line[field]]+1

            if field == group and line[field] not in group_list and len(group_list) <= 20:
                group_list.append(line[field])
# F is a list containining the fields that exist
# arg_f is the fields requested
#file name is provided to help with error message
def validate(f, arg_f, file_name):

    for arg in arg_f:
        try:
            f.index(arg)
        except:
            sys.stderr.write("Error: " + file_name +":no field with name \'"+ arg +"\'")
            sys.exit(8)



if __name__ == '__main__':
    main()
