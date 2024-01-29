import os

def list_uassets_in_dir(directory):
    uasset_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".uasset"):
                uasset_files.append(os.path.join(root, file))
    print(len(uasset_files))

# Example usage:
print("Lyra assets: ", list_uassets_in_dir(r"C:\Users\AnayDhaya\Documents\Unreal Projects\LyraStarterGame\Saved\Cooked\WindowsClient"))
print("Edison assets: ", list_uassets_in_dir(r"C:\dev\Python\Cooker Testing\Edison\Output\Saved\M2_LiveContent\Cooked\WindowsClient"))
print("M2Development assets: ", list_uassets_in_dir(r"C:\dev\M2Unreal\Game\M2Development\Saved\Cooked\WindowsClient"))