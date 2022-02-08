# Author:   Toylerrr
# Date:     June 14, 2021
# Description:  Install printer definition and other scripts for the Elegoo Neptune 2.
# License:  GPLv3

import os
import shutil
import errno

from UM.i18n import i18nCatalog
from UM.Extension import Extension
from UM.Logger import Logger
from UM.Message import Message
from UM.Application import Application
from UM.PluginRegistry import PluginRegistry
from UM.Resources import Resources 

from cura.Snapshot import Snapshot

catalog = i18nCatalog("cura")

class Installer(Extension):

    def __init__(self):
        super().__init__()
        self.setMenuName("Elegoo Neptune 2")
        self.addMenuItem(catalog.i18nc("@item:inmenu", "Install printer support"), self.installFiles)
        # Add a hook when a G-code is about to be written to a file
        Application.getInstance().getOutputDeviceManager().writeStarted.connect(self.add_snapshot_to_gcode)

        # Get a scene handler
        self.scene = Application.getInstance().getController().getScene()

    def installFiles(self, showMessage=True):
        Logger.log("i", "Installing printer support files (*.def.json, meshes and scripts) ...")

        # Local paths
        plugin_path = os.path.join(Resources.getStoragePath(Resources.Resources),
                "plugins", "ElegooNeptuneSupport")
        definitions_path = Resources.getStoragePath(Resources.DefinitionContainers)
        resources_path = Resources.getStoragePath(Resources.Resources)

        # Build src -> dst resource map
        resource_map = {
            #Printer Definitions
            "elegoo_neptune_2.def.json": {
                "src": os.path.join(plugin_path, "printer", "definitions"),
                "dst": os.path.join(definitions_path)
            },
            "elegoo_neptune_2D.def.json": {
                "src": os.path.join(plugin_path, "printer", "definitions"),
                "dst": os.path.join(definitions_path)
            },
            #Extruder Definition
            "elegoo_neptune2_extruder_0.def.json": {
                "src": os.path.join(plugin_path, "printer", "extruders"),
                "dst": os.path.join(resources_path, "extruders")
            },
            "elegoo_neptune2_extruder_1.def.json": {
                "src": os.path.join(plugin_path, "printer", "extruders"),
                "dst": os.path.join(resources_path, "extruders")
            },
            #Meshes
            "elegoo_neptune_2.stl": {
                "src": os.path.join(plugin_path, "printer", "meshes"),
                "dst": os.path.join(resources_path, "meshes")
            },
            #Quality
            "elegoo_neptune_2_draft.inst.cfg": {
                "src": os.path.join(plugin_path, "printer", "quality","elegoo_neptune_2"),
                "dst": os.path.join(resources_path,"quality","elegoo_neptune_2")
            },
            "elegoo_neptune_2_fine.inst.cfg": {
                "src": os.path.join(plugin_path, "printer", "quality","elegoo_neptune_2"),
                "dst": os.path.join(resources_path,"quality","elegoo_neptune_2")
            },
            "elegoo_neptune_2_normal.inst.cfg": {
                "src": os.path.join(plugin_path, "printer", "quality","elegoo_neptune_2"),
                "dst": os.path.join(resources_path,"quality","elegoo_neptune_2")
            },
            "elegoo_neptune_2D_draft.inst.cfg": {
                "src": os.path.join(plugin_path, "printer", "quality","elegoo_neptune_2D"),
                "dst": os.path.join(resources_path,"quality","elegoo_neptune_2D")
            },
            "elegoo_neptune_2D_fine.inst.cfg": {
                "src": os.path.join(plugin_path, "printer", "quality","elegoo_neptune_2D"),
                "dst": os.path.join(resources_path,"quality","elegoo_neptune_2D")
            },
            "elegoo_neptune_2D_normal.inst.cfg": {
                "src": os.path.join(plugin_path, "printer", "quality","elegoo_neptune_2D"),
                "dst": os.path.join(resources_path,"quality","elegoo_neptune_2D")
            }
        }

        # Copy all missing files from src to dst
        restart_required = False
        for f in resource_map.keys():
            src_dir, dst_dir = resource_map[f]["src"], resource_map[f]["dst"]
            src = os.path.join(src_dir, f)
            dst = os.path.join(dst_dir, f)
            if not os.path.exists(dst):
                Logger.log("i", "Installing resource '%s' into '%s'" % (src, dst))
                if not os.path.exists(dst_dir):
                    try:
                        os.makedirs(dst_dir)
                    except OSError as e:
                        if e.errno == errno.EEXIST and os.path.isdir(dst_dir):
                            pass
                        else:
                            raise
                shutil.copy2(src, dst, follow_symlinks=False)
                restart_required = True

        # Display a message to the user
        if showMessage:
            if restart_required:
                msg = catalog.i18nc("@info:status", "Neptune 2 files installed. Please restart Cura.")
            else:
                msg = catalog.i18nc("@info:status", "Neptune 2 files were already installed.")
            Message(msg).show()

        return
    # Takes a snapshot image and encodes it
    def create_snapshot(self, size):

        # Take a snapshot of given size
        snapshot = Snapshot.snapshot(width=size[0], height=size[1])

        # Used for debugging
        #snapshot.save(os.path.dirname(__file__) + "/test.png")

        # Snapshot gcode
        gcode = ''

        # Iterate all of the image  pixels
        for y in range(snapshot.height()):
            for x in range(snapshot.width()):

                # Take pixel data
                pixel = snapshot.pixelColor(x, y)

                # Convert to 16-bit (2-byte) -encoded image
                rgb16 = (pixel.red() >> 3 << 11) | (pixel.green() >> 2 << 5) | (pixel.blue() >> 3)

                # Convert pixel data into hex values
                rgb16_hex = "{:04x}".format(rgb16)

                # Change rndianess to little-endian
                rgb16_hex_le = rgb16_hex[2:4] + rgb16_hex[0:2]

                # Add resulting values to a gcode
                gcode += rgb16_hex_le

            # Add a G-code code
            gcode += '\rM10086 ;'

        # Add new line break
        gcode += '\r'

        # Return resulting G-code
        return gcode

    # G-code hook
    def add_snapshot_to_gcode(self, output_device):

        # If there's no G-code - return
        if not hasattr(self.scene, "gcode_dict") or not self.scene.gcode_dict:
            Logger.log("w", "Scene does not contain any gcode")
            return

        # Enumerate G-code objects
        for build_plate_number, gcode_list in self.scene.gcode_dict.items():
            for index, gcode in enumerate(gcode_list):

                # If there is ;gimage anywhere, add encoded snapshot image at the beginning
                if ';gimage' in gcode:
                    # Create a G-code
                    image_gcode = ';;gimage:' + self.create_snapshot((200, 200))
                    # Remove the tag
                    #self.scene.gcode_dict[build_plate_number][index] = self.scene.gcode_dict[build_plate_number][index].replace(';gimage', '')
                    # Add image G-code to the beginning of the G-code
                    self.scene.gcode_dict[0][0] = image_gcode + self.scene.gcode_dict[0][0]

                # If there is ;simage anywhere, add encoded snapshot image at the beginning
                if ';simage' in gcode:
                    # Create a G-code
                    image_gcode = ';simage:' + self.create_snapshot((100, 100))
                    # Remove the tag
                    #self.scene.gcode_dict[build_plate_number][index] = self.scene.gcode_dict[build_plate_number][index].replace(';simage', '')
                    # Add image G-code to the beginning of the G-code
                    self.scene.gcode_dict[0][0] = image_gcode + self.scene.gcode_dict[0][0]