# Uses ArcGIS data driven pages functionality to generate custom tiles for use with Google Maps

# This thing was my first real attempt at programming with ArcGIS and is an antique now, but back 
# in the day there weren't many good low-cost options to generate your own overlays for the 
# Google Maps API and we already had a basic ArcGIS license so we rolled with what we had.

# Google Maps is quite clever, individual images representing a tiny chunk of the map are
# organized in such a way that their folder name represents a y coordinate, while their file name
# represents an x coordinate; this enables fast retrieval by the API.  All we do here is use 
# ArcGIS to render the feature class, and save it the folder/file naming scheme Google Maps
# expects.

# Still could be used today, but two key modifications would be to:
#    1)  Calculate the map extent dynamically instead of relying on DDP grids to speed things up
#    2)  Refactor to just call the necessary GP/mapping functions directly (without using an MXD)
#        so that the Multiprocessing module can be taken advantage of.  Would reduce clunk factor
#        significantly.

#_______OBJECT CONSTRUCTOR_______________#
# Defines the map extent paremeters that we will need to render the tiles. The folder number (Y)
# and tile number (X) pararmeters are used to calculate the insertion point on Google Maps.  Its
# essential to get these right, otherwise the tiles won't render in the correct spot.
class InputVariables():
    def __init__(self, IIstartingFolderNum, IIendingFolderNum, IItileNum, IItilesPerRow, IItotalNumTiles):
        self.IIstartingFolderNum = IIstartingFolderNum  # y min
        self.IIendingFolderNum = IIendingFolderNum  # y max
        self.IItileNum = IItileNum  # x min
        self.IItilesPerRow = IItilesPerRow  # total x range/extent
        self.IItotalNumTiles = IItotalNumTiles  # total number of tiles we need to process
        

#_______INPUT OBJECTS___________________#
# Example of input object for zoom level 7 with Google Maps circa 2013.  Presumably, the convention
# is the same today.
ZL7 = InputVariables(52, 55, 4, 32, 4, 16)


#_______GENERATE TILES FUNCTION__________#
def createTiles(inputObject):
    #  Set MXD to the current, open mapping document
    mxd = arcpy.mapping.MapDocument("CURRENT")
    path = r"<your_path>\7\\"
    totalNumTiles = inputObject.IItotalNumTiles
    tilesPerRow = inputObject.IItilesPerRow
    startingFolderNum = inputObject.IIstartingFolderNum
    endingFolderNum = inputObject.IIendingFolderNum

    # Watermark added as a text element, degraded rendering performance less than other approaches
    text = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT") [0]	
    #  Keeps track of the cell in the DDP grid we're currently on.  DDP needs its own index
    currentCell = 0
    
    start_time = datetime.now()
    
    # Run until we've processed all the tiles we need to
    for tile in range (1, totalNumTiles):
        currentCell += 1
        iterationNum = 1
        # While we're within the acceptable y extent
        while startingFolderNum <= endingFolderNum:
            # For each increment in the y extent, set the initial tilenum/x value back to the min
            tileNum = inputObject.IItileNum
            # While we're within the upper bound for row/y range and also for the total number of tiles we want
            # to produce
            while currentCell <= tilesPerRow * iterationNum and currentCell <= totalNumTiles:
                # Uses DDP functionality to drive the changes in map extent from iteration to iteration.
                # Yes, this is gross and clunky.  Would not do it this way again.
                mxd.dataDrivenPages.currentPageID = currentCell
                # Prevents the repetion of the watermark for every tile
                if currentCell % 5 == 0:
                    text.elementPositionX = 0.5949
                else:
                    text.elementPositionX = 9
                # Exports the current cell/map extent as a PNG.  Assumes you've already set up the necessary folder structure
                arcpy.mapping.ExportToPNG(mxd, path + str(startingFolderNum) + "\\" + str(tileNum) + ".png", "", 256, 256, 32, False, "24-BIT_TRUE_COLOR", "255, 255, 255", "255, 255, 255", "False")
                tileNum = tileNum + 1
                currentCell = currentCell + 1
            iterationNum = iterationNum + 1
            startingFolderNum = startingFolderNum + 1
            
    complete_time = datetime.now()
    total_time = complete_time - start_time
 
    # Print some metrics   
    print("Start Time:  " + str(start_time))
    print("Completion Time:  " + str(complete_time))
    print("Total Processing Time:  " + str(total_time))
    print("Total Number of Tiles Produced:  " + str(totalNumTiles))
    
    # Delete the MXD object once we're done
    del mxd

createTiles(ZL7)
