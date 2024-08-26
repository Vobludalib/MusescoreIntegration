## Compiling the command-line arguments

Here is how the generated code works in terms of compiling a command-line call from the UI elements. You can follow along with the code in /Factory/templates.

I have a property (dictionary) called flags that stores the information about the command-line arguments. I found that the default values cannot be set when declaring this property, instead they are set in the onRun handler.

The flags dictionary is in the form: 
```
flags =  {"commandLineArg": { toPrint: true/false, value: "" },
.....}
```
The toPrint represents whether or not this specific command line argument and its associated value should be added to command line call, the value being the string to be passed as the value of the command-line argument.

The compilation of the command-line call occurs in the createCLICallFromFlags() function.

This function is hardcoded (by default, but you can change this in your generated code) to start the command-line call with python, followed by the script path, then the command-line arguments.

The command-line arguments are compiled by iterating over the flags dictionary. If the toPrint of a given command-line argument is true, then it is added to the call, along with its value. If the toPrint is false, it is skipped.

This approach was made to have as much modularity when adding/removing command-line arguments, hopefully having easy expandability.

## Reading/writing MusicXML files
Saving the currently opened Musescore score is handled inside createCLICallFromFlags() via:
```
var tempFilePath = mscTempFileStorePath.source + getCurrentTimeString();
writeScore(curScore, tempFilePath, "mxl");
call = call + ' --tempPath "' + tempFilePath + '.mxl"';
```
I have opted to have the filename be based on the current time, so as to not overwrite previous saved temp files, in case you need them. Again, this behaviour can be changed as deemed fit when you go to edit the created qml. A relevant function here is getCurrentTimeString().

The above code is only generated when readsScore is true in the JSON for generating the qml file.

Reading your MusicXML file into Musescore is handled inside buttonSave.onClicked()
```
var correctOutputPath = getLocalPath(String(output));
console.log('"' + correctOutputPath + '"');
readScore(correctOutputPath);
```
Don't forget, the output of your process that you call should output the path where the MusicXML file you create is stored.

The above code is generated only when writesScore is true in the JSON for generating the qml file.

## Setting the flags when interacting with UI elements
This is where I found things to be very finnicky, maybe some QML wizard can enlighten me why.

From the way I coded it, changing the flags dictionary is sometimes done inside the handlers related to the UI elements, sometime via seperate functions.

For example, for checkBoxes, the flags manipulation is done directly in the onClicked handler.

However, for fileDialogs, I have to create a boilerplated function to call each time inside the onAccepted handler, as for some reason doing the manipulation inside the handler did not persist. If things seem weird, console.log() is your friend here.

## Executing python scripts is weird
I have made sure that the code I generate makes the compilation to command-line calls correctly. I purposefully left the console.log() messages in where useful so you can verify this. However, for god-knows-what reason, even with a command-line call that works in the terminal run outside of Musescore, it sometimes just does not work. I would love to debug this, but because the Musescore QProcess API only exposes the 3 (yes 3!) most primitive functions, there is no real way to debug this. I have found that most things work on Windows 10 fairly well, with MacOS not working at all, and Linux being similarly messed up. **The things you write are likely to be platform-dependant in a way that is not nice.**

## Handling file paths
I have tried my best to write an OK-ish way of parsing different platform path notations (thanks Windows) using the getLocalPath(). This works well enough for the compilation to coammand-line args, but does not 100% work for the text for FileDialogs. If you deem fit, please make a version of this function that works properly.

Additionally, **if bugs crop up due to file paths**. It might be worth it to change the format of your file paths in your JSON that generates the QML, or mess around with the \\\ vs \ vs / in the code itself before you give it your end users.

## Links that helped me when trying to decipher QML:
A lot of the documentation for what I am trying to achieve is hidden deep-down in forum posts. There is little to no official documentation or support for this process calling, and it is likely subject to great change in Musescore 4, which I have not even dared looking at.

https://musescore.org/en/handbook/developers-handbook/plugins-3x
https://musescore.github.io/MuseScore_PluginAPI_Docs/plugins/html/class_ms_1_1_plugin_a_p_i_1_1_score.html
https://musescore.org/en/node/360446
https://musescore.org/en/node/344974
https://musescore.org/en/node/348558
https://musescore.org/en/print/book/export/html/76 - specifically the "log OS name, start another program commandline such as python" section

Great inspiration was taken initially from the abcImpEx plugin:
https://musescore.org/en/project/abc-importexport


If you set forth on the same journey of discovering how little documentation there is for this stuff, all I can say is:
```
 ________  ________  ________  ________          ___       ___  ___  ________  ___  __       
|\   ____\|\   __  \|\   __  \|\   ___ \        |\  \     |\  \|\  \|\   ____\|\  \|\  \     
\ \  \___|\ \  \|\  \ \  \|\  \ \  \_|\ \       \ \  \    \ \  \\\  \ \  \___|\ \  \/  /|_   
 \ \  \  __\ \  \\\  \ \  \\\  \ \  \ \\ \       \ \  \    \ \  \\\  \ \  \    \ \   ___  \  
  \ \  \|\  \ \  \\\  \ \  \\\  \ \  \_\\ \       \ \  \____\ \  \\\  \ \  \____\ \  \\ \  \ 
   \ \_______\ \_______\ \_______\ \_______\       \ \_______\ \_______\ \_______\ \__\\ \__\
    \|_______|\|_______|\|_______|\|_______|        \|_______|\|_______|\|_______|\|__| \|__|
                                                                                             
                                                                                             
                                                                                             
```