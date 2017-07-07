import subprocess as sp
import shutil
import sys
import string
import time
import os
import re
import matplotlib.pyplot as plt
import numpy as np

# Input of flap deflection angles.
delta1 = float(raw_input("Lower delta limit:") or 14)
delta2 = float(raw_input("Upper delta limit:") or 15)
dstep = float(raw_input("delta step length:") or 0.2)
airfoil = str(raw_input("Enter airfoil file name: ") or "naca632615.dat")
alfa = str(raw_input("Alfa (angle of attack of wing. default 2):") or 2)
flaphingexpos =  str(raw_input("Flap hinge x position: ") or 0.75)
bolcal = str(raw_input("Calculate roll helix angle? (y/n)") or "y")

outfile = "flaptest" + str(delta1) + "-"+ str(delta2) + "__" + str(time.strftime("%H_%M_%S")) + ".txt" 
zeroaoaoutfile = "zeroAOA"+ str(time.strftime("%H_%M_%S")) + ".txt"

# Starting sumprocess
#ps = sp.Popen(["xfoil.app/Contents/Resources/xfoil"],stdin=sp.PIPE,stdout=None,stderr=None)





try:
    ps = sp.Popen(["xfoil.exe"],stdin=sp.PIPE,stdout=None,stderr=None)
except OSError as e:
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
	issueCmd("load " + airfoil) # Load the dat file.
	issueCmd("MDES") # Go to the MDES menu.
	issueCmd("FILT") # Smooth any variations in the dat file data.
	issueCmd("EXEC") # Execute the smoothing.
	issueCmd("") # Back to main menu.
	issueCmd("PANE")

# Simulating airfoil for selected deltas.
def deltasim(airfoil, outfile, delta1, delta2, dstep, alfa):
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
		issueCmd("alfa" + alfa)
		issueCmd("")
	issueCmd("QUIT")

def alpha0sim(airfoil,zeroaoaoutfile):
	load_smooth(airfoil)
	issueCmd("OPER") # Go to the OPER menu.
	issueCmd("ITER 1000") # Max number of iterations set to 70 for convergence.
	issueCmd("RE 100000") # Set Reynolds number.
	issueCmd("VISC 100000") # Set viscous calculation with Reynolds number.

	issueCmd("PACC") # Enter PACC menu.
	issueCmd(zeroaoaoutfile) # Output file for xfoil polars.
	issueCmd("") # No buffer file.
	issueCmd("") #  Back to main menu.


	issueCmd("OPER")
	issueCmd("alfa 0")
	issueCmd("")
	issueCmd("PACC")
	issueCmd("VISC")
	issueCmd("QUIT")




# Running simulation.
alpha0sim(airfoil,zeroaoaoutfile)

try:
    ps = sp.Popen(["xfoil.exe"],stdin=sp.PIPE,stdout=None,stderr=None)
except OSError as e:
	ps = sp.Popen(["xfoil.app/Contents/Resources/xfoil"],stdin=sp.PIPE,stdout=None,stderr=None)

deltasim(airfoil, outfile, delta1, delta2, dstep, alfa)
ps.wait()

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
	cd0 = [row[2] for row in data_array]
	return [array, cd0]

# Plot Cl vs delta. Might miss Cl for some deltas since not always converging. This is ignored and thus the delta axis is not entierly true.
def plotClvd(outfile, delta1, delta2, dstep):
	clarray = getClarray(outfile)[0]
	length = len(clarray)
	clarray = np.array(clarray)

	# Making array shorter because of unconverged simulations.
	deltamax = delta1 + dstep * (length-1)
	newdvec = np.arange(delta1, deltamax + 0.01, dstep)

	# Number of unconverged simulations.
	noncon = len(np.arange(delta1, delta2 + 0.01, dstep)) - len(newdvec)
	print "\n"
	print "Number of delta angles with converged simulation: " + str(len(newdvec))
	print "Number of not converged simulations: " + str(noncon)


	# Linear fitting to obtain clda (/ deg).
	x = newdvec
	y = clarray

	fit = np.polyfit(x,y,1)
	cldadeg = fit[0]
	fit_fn = np.poly1d(fit) 

	if noncon == 0:
		print "clda (/ deg): " + str(cldadeg)
	else:
		print "Warning!!! Missing values of Cl since not converged"
		print "bad clda (/ deg): " + str(cldadeg)

	plt.plot(x,y, 'ro', x, fit_fn(x), '--k')
	
	plt.show()

	return cldadeg





# Plotting Cl vs delta.
cldadeg = plotClvd(outfile, delta1, delta2, dstep)


#_________________________________________________________________________________
# Calculation.

def setgeo():

	b = float(raw_input("Wing span: ") or 1.7)
	S = float(raw_input("Wing area: ") or 0.358)
	taper = float(raw_input("Wing taper: ") or 0.45)
	cord = float(raw_input("Wing cord: ") or 0.122)
	delta = float(raw_input("Max aileron deflection (degrees): ") or delta2)
	b1 = float(raw_input("Inner position: ") or 0.38)
	b2 = float(raw_input("Outer positien: ") or 0.8)

	deltarad = 2*np.pi*delta/360
	p = 2*(1-taper)

	return [b,S,taper,cord,delta,deltarad,p,b1,b2]

if (bolcal == "y"):

	[b,S,taper,cord,delta,deltarad,p,b1,b2] = setgeo()

	cda = 2*np.pi
	cd0 = getClarray(zeroaoaoutfile)[1][0]
	print "cd0:" + str(cd0)
	Clp = -4*(cda+cd0)/(S*b**2)*cord*((b**3)/(3*8)-(p/b)*(b**4)/(4*16))
	print "Clp:" + str(Clp)
	#Clp = -0.358
	cldarad = cldadeg*360/(2*np.pi)
	print "clda (/rad)" + str(cldarad)

	first = True
	while True:
		if first:
			first = False
		else:
			print "Try with new placement: (ctrl c to exit)"
			delta = float(raw_input("Max aileron deflection (degrees) (enter to keep unchanged (delta = " + str(delta) + "))") or delta)
			deltarad = 2*np.pi*delta/360
			print "Set position of aileron"
			b1 = float(raw_input("Inner position (enter to keep unchanged (b1 = " + str(b1) + ")): ") or b1)
			b2 = float(raw_input("Outer position (enter to keep unchanged (b2 = " + str(b2) + ")): ") or b2)

		Clda = (2*cldarad*cord/(S*b))*(((b2**2)/2-((p/b)*b2**3)/3)-((b1**2)/2-(p/b)*(b1**3)/3))
		rollhelixangle = -deltarad*Clda/Clp
		print "\n" + "Clda is: " 
		print str(Clda)
		print "Roll helik angle (rad): "
		print str(rollhelixangle)
		print "(Fighter 0.09, cargo/heavy transport 0.07"
		print "\n"


