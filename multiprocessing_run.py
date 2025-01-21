from multiprocessing import Process, Pool, cpu_count
import os
from neuron import h
import gc
import time 
# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)


from init_stim import run_simulation,save_plots


start=time.time()

def run_single_simulation(freq, amp):
    # Your simulation logic here
    # Replace the following with the actual simulation function call
    print(f"Running simulation for freq={freq}, amp={amp}")
    var="test_multiprocess"
    cell_id=1
    theta = 180
    phi = 0
    simtime = 1000
    dt = 0.001
    depth = 1
    modfreq = 10
    ton = 0
    dur = simtime
    run_id = 0
    cb=True
    ramp=True
    ramp_duration=400
    tau=0
    data_dir="/media/sf_Data"
    try:
        e_dir,t, is_xtra,vrec,soma_v,dend_v,axon_v,cell=run_simulation(cell_id, theta, phi, simtime, dt, amp, depth, freq, modfreq,
                                                               ton,dur,run_id,cb,var,ramp,ramp_duration,tau,data_dir)
        save_plots(e_dir, t, is_xtra, vrec, soma_v, dend_v)
    except Exception as e:
        print(f"Error during simulation for freq={freq}, v_plate={amp}: {e}")
    finally:
        # Cleanup
        h("forall delete_section()")
        gc.collect()


if __name__ == '__main__':
    
    num_processes = cpu_count()

    v_values = [10, 20]
    CFreqs = [100]

    inputs = [(freq, amp) for freq in CFreqs for amp in v_values]
    # processes = []

    # for freq in CFreqs:
    #     for amp in v_values:
    #         p = Process(target=run_single_simulation, args=(freq, amp))
    #         p.start()
    #         processes.append(p)

    # for p in processes:
    #     p.join()
    # Use a Pool to parallelize simulations

    with Pool(processes=num_processes) as pool:
        # Run simulations in parallel
        pool.starmap(run_single_simulation, inputs)

end=time.time()
print(f"The time of execution of above program is : {end-start} s")
print(f"The time of execution of above program is : {(end-start)/60} mins")

