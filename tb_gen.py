import re
import sys, getopt
import os.path
from collections import OrderedDict
    
def get_module(file_name, search_depth=9999):
    '''extracts: module module_name (.... );'''
    mext='module\s+\w+\W+\([^;]+'
    with open(file_name) as f:
        chars = f.read(search_depth)
        match = re.findall(mext, chars)
    if len(match) == 0:
        print("Couldn't find module")
        sys.exit(1)
    return match[0]

def strip_comments(chars):
    # Strips any line starting with //    
    lines = chars.splitlines()
    is_comment = '^\s*\/\/'
    retlines = []
    for line in lines:
        if not re.findall(is_comment, line) and (len(line.split()) > 0):
            retlines.append(line)
    return retlines

def name_parse(frags):
    net_types = ['wire','reg','logic']
    name, size = '',''
    for frag in frags:
        if frag in net_types:
            pass
        elif frag[0] == '[':
            size += frag
        else:
            name = frag.replace(',','')
            return name, size

def parse_module(module):
    module_lines = strip_comments(module)
    module_name = module_lines.pop(0).split()[1]
    inputs = OrderedDict()
    outputs = OrderedDict()
    for line in module_lines:
        frag = line.split()
        if frag[0] == 'input':
            name, size = name_parse(frag[1:])
            inputs[name] = size
        elif frag[0] == 'output':
            name, size = name_parse(frag[1:])
            outputs[name] = size
            
    return inputs, outputs, module_name

def write_header(name, f):
    f.write("`timescale 10 ns / 100 ps\n\n")
    f.write('module ' + name + '_tb;\n\n')
    
def write_signals(inputs, outputs, f):
    def write_group(signals, f):
        max_size = max(map(len, signals.values()))
        for name, size in signals.iteritems():
            pad = max_size - len(size)
            f.write(' '.join(['logic', size, ' '*pad, name]) + ';\n')
    f.write('// inputs\n')
    write_group(inputs, f)        
    f.write('\n// outputs\n')
    write_group(outputs, f)

def write_module(inputs, outputs, n, f):
    f.write('\n\n// Instantiate DUT\n')
    f.write(' '.join([n, n+'_inst', '(\n']))
    # connect signals
    signals = inputs.keys() + outputs.keys()
    maxlen = max(map(len, signals))
    for i, name in enumerate(signals):
        blanks = ' '*(maxlen - len(name))
        f.write('  .{0}{1} ({0}{1})'.format(name, blanks))
        if i < len(signals)-1:
            f.write(',\n')
    f.write(');\n')
    
def parse_args(argv):
    usage = argv[0] + ' -i <inputfile> -o (optional) <outputfile>'
    inputfile = ''
    outputfile = ''
    
    try:
        opts, args = getopt.getopt(argv[1:],"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print usage
        sys.exit(2)
    if not opts:
        print usage
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print usage
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
    return inputfile, outputfile

if __name__ == "__main__":
    ifile, tb_name = parse_args(sys.argv)
    if not ifile:
        print "No input file?"
        sys.exit()
    m = get_module(ifile)
    if not m:
        print ("Couldn't extract a module(...);")
        sys.exit(1)
    ins, outs, name = parse_module(m)
    if not tb_name:
        tb_name = name + '_tb.sv' 
    if os.path.isfile(tb_name):
        ans = raw_input("%s exists! Overwrite?\n" % tb_name)
        if len(ans) < 1 or ans.lower()[0] != 'y':
            print("Aborting generation!")
            sys.exit(0)
    with open(tb_name, 'w') as f:
        write_header(name, f)
        write_signals(ins, outs, f)
        write_module(ins, outs, name, f)
        
    print("Generated %s" % tb_name)