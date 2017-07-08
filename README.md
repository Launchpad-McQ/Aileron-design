# flapstest
## What it does:
  Helps you to calculate your aileron position and size for airplanes in small reynolds numbers (limitation of xfoil) such as RC planes. It will give you a roll helix angle which tells you your sustained roll capability. 
  
## How to use:
1. Put flapstest.py in same folder as your airfoil.dat file, xfoil.exe or (xfoil.app for mac os x users).

  (You can find airfoil.dat files at http://airfoiltools.com)
  (You can download xfoil at http://web.mit.edu/drela/Public/web/xfoil/)
  
2. Run the python script and it will be self explanatory. (Written in python 2.7)

  You can stop the script with ctrl-c at any time.

  (You can skip input and use default by just pressing enter when prompted for input)
  
  In the graph that appears you want a got fit between the line and dots since the slope of this line is Change in lift coefficient with aileron deflection. You also probably want to have all simulations to have converged or the aileron effectiveness will be a little overestimated.

* If you want to design ailerons you want "Upper delta limit" to be your maximum downward aileron angle and "Lower delta limit" to be close to your maximum downward aileron angle.
