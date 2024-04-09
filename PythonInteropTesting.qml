import QtQuick 2.9
import QtQuick.Dialogs 1.0
import QtQuick.Controls 1.0
import MuseScore 3.0
import FileIO 3.0

MuseScore {
	menuPath: "Plugins.PythonServerInterop"
	version: "0.1"
	id:window
	width: 800; height: 500;
	requiresScore: false
	pluginType: "dialog"

	onRun: {}

	FileIO {
		id: mscTempXmlFile
		source: tempPath() + "/mscTempXmlFile.xml"
		onError: console.log(msg)
	}

	Button {
		id: buttonSave
		text: qsTr("Send to Python server")
		anchors.left: window.left

		onClicked: {
			// writeScore(curScore, mscTempXmlFile.source, "xml");
			// var content = "content=" + encodeURIComponent("YOYOYO");
			var urlToServer = "http://127.0.0.1:" + serverPort();
			var requestValue = "/plugin";
			var sendUrl = urlToServer + requestValue;

			console.log(sendUrl);
			var request = new XMLHttpRequest();
			request.onreadstatechange = function() {
			if (request.readyState == XMLHttpRequest.Done)
			{
				var response = request.responseText
				console.log("responseText : " + response);
				// myFile.write(response)
				// readScore(myFile.source)
				// Qt.quit()
			}
			request.open("GET", sendUrl, true);
			// request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded")
			request.send();
		}
	}


	function serverPort()
	{
		return "5000";
	}
}
}