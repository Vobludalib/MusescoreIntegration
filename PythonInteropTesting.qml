import QtQuick 2.0
import QtQml 2.8
import MuseScore 3.0

MuseScore {
      menuPath: "Plugins.pluginName"
      description: "Description goes here"
      version: "1.0"
      QProcess { id: proc }
      onRun: {
            proc.start('/bin/sh -c "code"');
      }
}