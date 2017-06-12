import sesame
import numpy as np


# dimensions of the system
Lx = 3e-6 #[m]
Ly = 5e-6 #[m]

# extent of the junction from the left contact [m]
junction = 10e-9 

# Mesh
x = np.concatenate((np.linspace(0,1.2e-6, 150, endpoint=False), 
                    np.linspace(1.2e-6, Lx, 50)))
y = np.concatenate((np.linspace(0, 2.25e-6, 50, endpoint=False), 
                    np.linspace(2.25e-6, 2.75e-6, 50, endpoint=False),
                    np.linspace(2.75e-6, Ly, 50)))

# Create a system
sys = sesame.Builder(x, y)

def region(pos):
    x, y = pos
    return x < junction

# Add the donors
nD = 1e17 * 1e6 # [m^-3]
sys.add_donor(nD, region)

# Add the acceptors
region2 = lambda pos: 1 - region(pos)
nA = 1e15 * 1e6 # [m^-3]
sys.add_acceptor(nA, region2)

# Use perfectly selective contacts
Sn_left, Sp_left, Sn_right, Sp_right = 1e50, 0, 0, 1e50
sys.contacts(Sn_left, Sp_left, Sn_right, Sp_right)

def region1(pos):
    x, y = pos
    return (y < 2.4e-6) | (y > 2.6e-6)

# Dictionary with the material parameters
reg1 = {'Nc':8e17*1e6, 'Nv':1.8e19*1e6, 'Eg':1.5, 'epsilon':9.4,
        'mu_e':200*1e-4, 'mu_h':200*1e-4, 'tau_e':10e-9, 'tau_h':10e-9}

# Add the material to the system
sys.add_material(reg1, region1)

# Dictionary with the material parameters
reg2 = {'Nc':8e17*1e6, 'Nv':1.8e19*1e6, 'Eg':1.5, 'epsilon':9.4,
        'mu_e':20*1e-4, 'mu_h':20*1e-4, 'tau_e':10e-9, 'tau_h':10e-9}

# Add the material to the system
sys.add_material(reg2, lambda pos: 1 - region1(pos))

# gap state characteristics
s = 1e-15 * 1e-4         # trap capture cross section [m^2]
E = -0.25                # energy of gap state (eV) from midgap
N = 2e13 * 1e4           # defect density [1/m^2]

# Specify the two points that make the line containing additional charges
p1 = (20e-9, 2.5e-6)   #[m]
p2 = (2.9e-6, 2.5e-6)  #[m]

# Pass the information to the system
sys.add_line_defects([p1, p2], N, s, E=E)


sesame.plot(sys, sys.mu_e)

sesame.plot_line_defects(sys)
