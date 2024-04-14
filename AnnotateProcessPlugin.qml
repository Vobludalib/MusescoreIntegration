import QtQuick 2.9
import QtQuick.Dialogs 1.0
import QtQuick.Controls 1.0
import MuseScore 3.0
import FileIO 3.0

MuseScore {
	menuPath: "Plugins.AnnotateTopVoiceInPython"
	version: "0.1"
	id:window
	width: 800; height: 500;
	requiresScore: true
	pluginType: "dialog"

	QProcess {
		id: proc
	}

	onRun: {}

	FileIO {
		id: mscTempXmlFile
		source: "C:\\Users\\simon\\OneDrive\\Desktop\\Coding Projects\\MusescoreIntegration\\temp" + "\\mscTempXmlFile.xml"
		onError: console.log(msg)
	}

	Button {
		id: buttonSave
		text: qsTr("Annotate")
		anchors.left: window.left

		onClicked: {
			writeScore(curScore, mscTempXmlFile.source, "xml");
			proc.start('python "C:\\Users\\simon\\OneDrive\\Desktop\\Coding Projects\\MusescoreIntegration\\Music21Exploration\\AnnotateTopVoice.py" ' + mscTempXmlFile.source);
			var val = proc.waitForFinished(100);
			console.log("Finished python script");
			readScore("C:\\Users\\simon\\OneDrive\\Desktop\\Coding Projects\\MusescoreIntegration\\temp\\tempColoured.mxl");
		}
	}
}