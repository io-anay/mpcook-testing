import os
import subprocess
import time
import psutil
import shutil
from plot_data import execute
from monitor_hardware import monitor_usage, monitor_baseline_usage, plot_smoothed_data

#define structure containing all the info to run this with a different project
class ProjectInfo:
    def __init__(self, projectPath, plugin, mapArgument, UnrealRoot=None, DDCPath=None):
        self.projectPath = projectPath
        self.plugin = plugin
        self.buildPackageId = "multi-process-cook-test"
        self.baseReleaseTempDirectory = "C:\dev\Python\Cooker Testing\ReleaseTemp"
        self.outputDir = f"C:\dev\Python\Cooker Testing\{plugin}\Output\Saved\M2_LiveContent"
        self.clientPlatforms = "Win64+Linux"
        self.serverPlatforms = "Linux"
        self.mapArgument = mapArgument
        self.UnrealRoot = UnrealRoot
        self.DDCPath = DDCPath

# Define M2Development and Edison ProjectInfos as enum that can be chosen from
class ProjectInfos:
    M2Development = ProjectInfo("C:\dev\M2Unreal\Game\M2Development\M2Development.uproject", "WorldTravelTest", "Skypark_P+ApproachabilityGym+VoxelWorld+NatCommTestGym+WorldTravelTestMap+WorldTravelTestMap_2")
    Edison = ProjectInfo("C:\dev\Edison-main\Edison\Edison.uproject", "Edison", "/Edison/Events/BasketballJan24/Maps/Basketball_P+/Edison/Maps/Edison_P+Edison/Events/Halloween2023/Hallow_P+Edison/Events/Runner/Maps/Runner_P")
    Lyra = ProjectInfo("C:\\Users\\AnayDhaya\\Documents\\Unreal Projects\\LyraStarterGame\\LyraStarterGame.uproject", "ShooterMaps", "/ShooterMaps/Maps/L_Expanse", r"C:\Program Files\Epic Games\UE_5.3\Engine", r"C:\\Users\\AnayDhaya\\AppData\\Local\\UnrealEngine\\Common\\DerivedDataCache")

def main():

    # Create directory for logs for this execution of the script if it doesnt exist
    logs_dir_root = "./Logs/get_unreal_cook_stats_{}".format(time.strftime("%Y%m%d-%H%M%S"))
    if not os.path.exists(logs_dir_root):
        os.makedirs(logs_dir_root)

    # System specs
    # Get the RAM information
    ram_info = psutil.virtual_memory()
    print("=====================================")
    print("System Specs:")
    print("CPU: " + os.environ['PROCESSOR_IDENTIFIER'])
    print("Physical cores:", psutil.cpu_count(logical=False))
    print("Total cores:", psutil.cpu_count(logical=True))
    print("Total RAM: {0} GB".format(ram_info.total / (1024.0 ** 3)))
    print("Available RAM: {0} GB".format(ram_info.available / (1024.0 ** 3)))
    print("Used RAM: {0} GB".format(ram_info.used / (1024.0 ** 3)))
    print("=====================================")

    # ===============================
    # == CONFIGURE THE SCRIPT HERE ==
    # ===============================

    # User selects which project to run
    project = ProjectInfos.M2Development

    # User selects how to run the script
    deleteDDC = False
    useDDCArg = True
    useCleanArg = False
    runJunoLiveCookUpload = False
    MonitorHardwareUsage = True
    cookAllProject = True

    # User chooses the number of processes to test. Each entry is tested num_repeats times
    tests_to_run = [1]
    num_repeats = 1

    # ===============================
    # == CONFIGURE THE SCRIPT HERE ==
    # ===============================

    # If using JunoLiveCookUpload then use the packaged editor
    if runJunoLiveCookUpload:
        UnrealRoot = r"C:\Users\AnayDhaya\AppData\Local\M2Launcher\Editors\69bcc3\Windows\Engine"
        ddc_path = r"C:\\Users\\AnayDhaya\\AppData\\Local\\UnrealEngine\\Common\\DerivedDataCache"
    else:
        UnrealRoot = r"C:\dev\M2Unreal\Game\Engine"
        ddc_path = "C:\\dev\\M2Unreal\\Game\\Engine\\DerivedDataCache"
        # UnrealRoot = r"C:\Program Files\Epic Games\UE_5.1\Engine"
        # ddc_path = r"C:\\Users\\AnayDhaya\\AppData\\Local\\UnrealEngine\\Common\\DerivedDataCache"

    # Project unreal overwrites these
    if project.UnrealRoot:
        UnrealRoot = project.UnrealRoot
    if project.DDCPath:
        ddc_path = project.DDCPath

    UnrealExe = os.path.join(UnrealRoot, "Binaries/Win64/UnrealEditor-Cmd.exe")
    UATPath = os.path.join(UnrealRoot, "Build/BatchFiles/RunUAT.bat")

    # Run stats storage
    run_data_file = logs_dir_root + "/run_data.txt"
    run_data = {}

    # Get the baseline CPU and memory usage
    if MonitorHardwareUsage:
        print("Monitoring CPU and memory usage...")
        baseline_cpu, baseline_memory = monitor_baseline_usage(10000)

    # Write all the variables to a file so we can see what the script was run with
    with open(logs_dir_root + "/run_variables.txt", "w") as f:
        f.write("projectPath: " + project.projectPath + "\n")
        f.write("UnrealRoot: " + UnrealRoot + "\n")
        f.write("UnrealExe: " + UnrealExe + "\n")
        f.write("UATPath: " + UATPath + "\n")
        f.write("BuildPackageId: " + project.buildPackageId + "\n")
        f.write("BaseReleaseTempDirectory: " + project.baseReleaseTempDirectory + "\n")
        f.write("ClientPlatforms: " + project.clientPlatforms + "\n")
        f.write("ServerPlatforms: " + project.serverPlatforms + "\n")
        f.write("MapArgument: " + project.mapArgument + "\n")
        f.write("NumProcessesToTest: " + str(tests_to_run) + "\n")
        f.write("NumRepeatsEachTest: " + str(num_repeats) + "\n")
        f.write("DeleteDDC: " + str(deleteDDC) + "\n")
        f.write("UseDDCArg: " + str(useDDCArg) + "\n")
        f.write("UseCleanArg: " + str(useCleanArg) + "\n")
        f.write("RunJunoLiveCookUpload: " + str(runJunoLiveCookUpload) + "\n")
        f.write("MonitorHardwareUsage: " + str(MonitorHardwareUsage) + "\n")

        if MonitorHardwareUsage:
            f.write("------------------------------------------------------------------\n")
            f.write("baseline_cpu: " + str(baseline_cpu) + "\n")
            f.write("baseline_memory: " + str(baseline_memory) + "\n")
        
    for test_num_processes in tests_to_run:       
        print("\n--------------------\n-- Testing multiprocess: " + str(test_num_processes) + " --\n--------------------")
        
        # Add value to dictionary where num_processes is the key
        run_data[test_num_processes] = []

        # Create directory for logs for this number of processes if it doesnt exist
        logs_dir = logs_dir_root + "/num_processes_{}".format(test_num_processes)
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        # Repeat this test num_repeats times
        for repeat_num in range(num_repeats):

            # Optional delete the ddc directory
            if deleteDDC:
                if os.path.exists(ddc_path):
                    shutil.rmtree(ddc_path)

            # Prepare the base command, either the junolivecookupload with skipupload as it is ran from CI or the normal command which is ran when packaging an editor build with skippackage
            if runJunoLiveCookUpload:
                command = [UATPath, "JunoLiveCookUpload", 
                    "-project=\"" + project.projectPath + "\"", 
                    "-packagetarget=Win64.Client.Development+Linux.Client.Development+Win64.Client.Test+Linux.Client.Test+Linux.Server.Test+Win64.Client.Shipping+Linux.Client.Shipping", 
                    "-unrealexe=" + UnrealExe, 
                    "-releaseversion=" + project.buildPackageId, 
                    "-releaseversionroot=" + project.baseReleaseTempDirectory, 
                    "-plugin=" + project.plugin, 
                    "-UploadId=\"anaytest\"", 
                    "-skipupload", 
                    "-outputdir=" + project.outputDir,
                    "-AdditionalMapsToCook=\"" + project.mapArgument + "\"", 
                    "-OverrideMapsToCook=\"" + project.mapArgument + "\"", 
                    "-mpcookprocesscount=" + str(test_num_processes)]
            else:
                # command = [UATPath, "BuildCookRun", "-nop4", "-cook", "-skipstage", "-prereqs", "-compressed", "-ddc", "-project=" + projectPath, "-skippackage", "-createreleaseversion=" + buildPackageId, "-createreleaseversionroot=" + baseReleaseTempDirectory, "-skipbuild", "-skipbuildeditor", "-nocompile", "-installed", "-utf8output", "-waitmutex", "-SkipCookingEditorContent", "-client", "-TargetPlatform=" + clientPlatforms, "-server", "-ServerTargetPlatform=" + serverPlatforms, "-AdditionalCookerOptions=\"-cookprocesscount=" + str(num_processes) + "\"", "-map=" + mapArgument]
                command = [UATPath, "BuildCookRun", "-nop4", "-cook", "-skipstage", "-prereqs", "-compressed",
                    "-project=\"" + project.projectPath + "\"", 
                    "-skippackage", 
                    "-createreleaseversion=\"" + project.buildPackageId + "\"", 
                    "-createreleaseversionroot=" + project.baseReleaseTempDirectory, 
                    "-skipbuild", "-skipbuildeditor", "-nocompile", "-installed", "-utf8output", "-waitmutex", "-SkipCookingEditorContent", 
                    "-client", 
                    "-TargetPlatform=" + project.clientPlatforms, 
                    "-server", 
                    "-ServerTargetPlatform=" + project.serverPlatforms, 
                    "-AdditionalCookerOptions=\"-cookprocesscount=" + str(test_num_processes) + "\"", 
                    "-map=\"" + project.mapArgument + "\""]

            # Optional clean intermediate and saved directories
            if useCleanArg:
                command.insert(2, "-clean")

            # Optional add -ddc command to the command
            if useDDCArg:
                command.insert(2, "-ddc")

            # Remove -map argument if cookAllProject is True
            if cookAllProject:
                command = [arg for arg in command if not arg.startswith("-map")]

            # Use subprocess.run to call UAT as if from command line with some additinalcookeroptions for the projectPath. Log the output to a file.
            start_time = time.time()
            if MonitorHardwareUsage:
                result = monitor_usage(command, logs_dir, os.path.join(logs_dir, f"run_{repeat_num + 1}.txt"), repeat_num)
            else:
                print("\n>> Running: " + ' '.join(command))
                result = subprocess.run(command, stdout=open(os.path.join(logs_dir, f"run_{repeat_num + 1}.txt"), "w"))
            end_time = time.time()
    
            if result.returncode == 0:
                print("     Command executed successfully.")
            else:
                print("     Command failed with return code: ", result.returncode)
                break
    
            # Print the time it took to cook
            print("     Cooking took " + str(end_time - start_time) + " seconds.")
            run_data[test_num_processes].append(end_time - start_time)

            # Each time a run completes and the data is added to the run_data dictionary, write the data to a file overwriting the previous data. This acts as protection against crashes or if we want to end the script early.
            with open(run_data_file, "w") as f:
                f.write(str(run_data))

        # Use all the usage_data.json files to plot the data. Find the files that are inside the logs_dir and start with the name usage_data
        json_files = [os.path.join(logs_dir, f) for f in os.listdir(logs_dir) if os.path.isfile(os.path.join(logs_dir, f)) and f.startswith("usage_data")]
        plot_smoothed_data(json_files, f"CPU(blue) and Memory(red) usage for {test_num_processes} processes", logs_dir, baseline_cpu=baseline_cpu, baseline_memory=baseline_memory)   

    # Find all files in logs_dir_root and subdirs that start with usage_data and plot the data
    if len(tests_to_run) > 1:
        json_files = [os.path.join(root, f) for root, dirs, files in os.walk(logs_dir_root) for f in files if f.startswith("usage_data")]
        plot_smoothed_data(json_files, f"Overlay plot of CPU and Memory usage for all tested number of processes", logs_dir_root, baseline_cpu=baseline_cpu, baseline_memory=baseline_memory)
                
    # print the data
    print("\nData:")
    print(run_data)
            
    # plot the data
    execute(run_data)

    print("\nStopping...\n")

main()