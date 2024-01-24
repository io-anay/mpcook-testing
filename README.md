# mpcook-testing

- Make sure you update the ProjectInfo and ProjectInfos as the top of get_unreal_cook_stats.py to point to your own projects and engine installs
- Change the DDC path to match your common path and your M2Unreal path
- Configure the run by changing:
- - deleteDDC - will delete the DDC so that you get a long cook
- - useDDCArg - (not sure this does anything?) but was testing to see if it was an alternative to deleting the DDC each time. So far doesnt seem to have worked
- - useCleanArg - (only works when doing a BuildCookRun command - runJunoLiveCookUpload=False). Will clean the Saved and Intermediates before each run
- - runJunoLiveCookUpload - will use the JunoLiveCookUpload commandlet rather than buildcookrun in UAT. This is basically the difference between the command ran when an editor is packaged (FALSE) vs when content is cooked in project-ci (TRUE)
- - MonitorHarwareUsage - will record the baseline at the start of the run and plot the CPU and Memory usages over time while the cooking happens
 
Once that configs done, should be as simple as cd'ing into the dir and then running python python get_unreal_cook_stats.py

** If you are using DDC and not deleting the DDC then you need to run one pass first otherwise you will have a long run followed by short ones ** 
