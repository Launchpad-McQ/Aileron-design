import subprocess as sp
import shutil
import sys
import string
import time
import os
import re
import matplotlib.pyplot as plt
import numpy as np
from sklearn import datasets, linear_model

# Input of flap deflection angles.
delta1 = float(raw_input("Lower delta limit:") or 14)
delta2 = float(raw_input("Upper delta limit:") or 14.4)
dstep = float(raw_input("delta step length:") or 0.2)
airfoil = str(raw_input("Enter airfoil file name: ") or "load naca632615.dat")
flaphingexpos =  str(raw_input("Flap hinge x position: ") or 0.75)

outfile = "flaptest" + str(delta1) + "-"+ str(delta2) + "__" + str(time.strftime("%H_%M_%S")) + ".txt" 

# Starting sumprocess
ps = sp.Popen(["xfoil.app/Contents/Resources/xfoil"],stdin=sp.PIPE,stdout=None,stderr=None)



def my_range(start, end, step):
    while start <= end:
        yield start
        start += step


def issueCmd(cmd, echo=True):
    ps.stdin.write(cmd+'\n')
    if echo:
    	print cmd

# Setting flap deflection.
def setflap(delta):
	issueCmd("GDES") # Geometry design routine.
	issueCmd("flap") # Deflect trailing edge flap.
	issueCmd(flaphingexpos) # Enter flap hinge x location.
	issueCmd("999") # Enter flap hinge y location (or 999 to specify y/t).
	issueCmd("0.5") # Enter flap hinge relative y/t location   r>  0.5.
	issueCmd(delta) # Enter flap deflection in degrees (+ down)   r>  15.
	issueCmd("eXec") # Set current airfoil <== buffer  airfoil.
	issueCmd("")

# Loading airfoil.
def load_smooth(airfoil):
	issueCmd(airfoil) # Load the dat file.
	issueCmd("MDES") # Go to the MDES menu.
	issueCmd("FILT") # Smooth any variations in the dat file data.
	issueCmd("EXEC") # Execute the smoothing.
	issueCmd("") # Back to main menu.

# Simulating airfoil for selected deltas.
def deltasim(airfoil, outfile, delta1, delta2, dstep):
	load_smooth(airfoil)
	issueCmd("OPER") # Go to the OPER menu.
	issueCmd("ITER 1000") # Max number of iterations set to 70 for convergence.
	issueCmd("RE 100000") # Set Reynolds number.
	issueCmd("VISC 100000") # Set viscous calculation with Reynolds number.

	issueCmd("PACC") # Enter PACC menu.
	issueCmd(outfile) # Output file for xfoil polars.
	issueCmd("") # No buffer file.
	issueCmd("") #  Back to main menu.

	for delta in my_range(delta1, delta2, dstep):
		load_smooth(airfoil)
		setflap(str(delta))
		issueCmd("OPER")
		issueCmd("alfa 2")
		#time.sleep(1)
		issueCmd("")
	issueCmd("QUIT")



#__________________________________________________________________________________________
# Plotting C_l vs delta

def clean_split(s): return re.split('\s+', s.replace(os.linesep,''))[1:]

def getClarray(outfile):
	with open(outfile, "r") as ins:
	    lines = []
	    for line in ins:
	        lines.append(line)




	# Find location of data from ---- divider
	for i, line in enumerate(lines):
	    if re.match('\s*---', line):
	        dividerIndex = i


	# What columns mean
	data_header = clean_split(lines[dividerIndex-1])

	# Clean info lines
	info = ''.join(lines[dividerIndex-4:dividerIndex-2])
	info = re.sub("[\r\n\s]","", info)
	# Parse info with regular expressions
	def p(s): return float(re.search(s, info).group(1))
	infodict = {
	 'xtrf_top': p("xtrf=(\d+\.\d+)"),
	 'xtrf_bottom': p("\(top\)(\d+\.\d+)\(bottom\)"),
	 'Mach': p("Mach=(\d+\.\d+)"),
	 'Ncrit': p("Ncrit=(\d+\.\d+)"),
	 'Re': p("Re=(\d+\.\d+e\d+)")
	}

	# Extract, clean, convert to array
	datalines = lines[dividerIndex+1:]
	data_array = np.array(
	[clean_split(dataline) for dataline in datalines], dtype='float')


	# Extracting Cl.
	array = [row[1] for row in data_array]
	return array


# Plot Cl vs delta. Might miss Cl for some deltas since not always converging. This is ignored and thus the delta axis is not entierly true.
def plotClvd(outfile, delta1, delta2, dstep):
	clarray = getClarray(outfile)
	length = len(clarray)


	# Making array shorter because of unconverged simulations.
	deltamax = delta1 + dstep * (length-1)
	newdvec = np.arange(delta1, deltamax + 0.01, dstep)

	# Number of unconverged simulations.
	noncon = len(np.arange(delta1, delta2 + 0.01, dstep)) - len(newdvec)
	print "\n"
	print "Number of delta angled with converged simulation: " + str(len(newdvec))
	print "Number of not converged simulations: " + str(noncon)



	plt.plot(newdvec,np.array(clarray),'bo')

	plt.ylabel('C_l')
	plt.xlabel('\delta')
	plt.show()




# Running simulation.
deltasim(airfoil, outfile, delta1, delta2, dstep)
ps.wait()

# Plotting Cl vs delta.
plotClvd(outfile, delta1, delta2, dstep)