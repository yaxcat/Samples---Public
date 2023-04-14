# A few functions to deal with basic raster operations like resampling and flattening
# ____________________________________________________________________________________________________


class BasicRasterOperations:
    # Intended to store real world map coordinates
    def __init__(self, y: float, x: float, z: float, m: float):
        self.y = y
        self.x = x
        self.z = z
        self.m = m

    # Converts 2 dimensional local raster coordaintes to 1 dimensional index IDs. Useful for working with
    # flattened arrays
    def convert_coords_to_one_dim(col: int, row: int, pixels_per_row: int):
        pixel_index = col + (row * pixels_per_row)
        return pixel_index

    # Converts 1D index ID back into local 2D coordinates
    def convert_one_dim_to_coords(pixel: int, pixels_per_row: int):
        row = pixel // pixels_per_row
        col = pixel % pixels_per_row
        return col, row

    # Scaling function to resample from high resolution to a lower resolution
    def resample_to_lower_resolution(
        col: int, row: int, pixels_per_row_scaled: int, pixel_size_scaled: int
    ):
        # Check to make sure scaling factor isn't zero
        if pixel_size_scaled == 0:
            raise ValueError(
                "Scaling factor cannot be zero, it will create a singularity and destroy the Earth."
            )
        scale_col = col // pixel_size_scaled
        scale_row = row // pixel_size_scaled
        course_pix = BasicRasterOperations.convert_coords_to_one_dim(
            scale_row, scale_col, pixels_per_row_scaled
        )
        return course_pix

    # Resamples from a low resolution to a higher resolution, returns the center point of the
    # low resolution pixel in high resolution coordinates
    def resample_to_higher_resolution(input_pixel_size: int, col: int, row: int):
        cen_col = col * input_pixel_size + (input_pixel_size // 2)
        cen_row = row * input_pixel_size + (input_pixel_size // 2)
        return cen_col, cen_row

    # Transforms projected real world coordinates into row/column coordinates useful when having to
    # work in a raster's naive, local coordinate system
    def convert_real_coord_to_local(
        x: float, y: float, total_rows: int, origin: object, offset: float
    ):
        col_pad = int(origin.x + offset)
        row_pad = int(origin.y + offset)
        col = x - col_pad - 1
        row = total_rows - (y - row_pad)
        return col, row

    # Transforms naive local raster coordinates into real world coordinates using a coordinate
    # object
    def convert_local_coord_to_real(row: int, col: int, origin: object, offset: float):
        col_pad = origin.x + offset
        row_pad = origin.y + offset
        x = col + col_pad + 1
        y = row_pad - row
        return x, y

    # Calculates as-the-crow-flies distance to a surface destination. Can be used in cost path determination,
    # among other things. Changes the value of the items in the input array directly and as such has
    # no return value
    def calc_euclidean_dist(
        top_row_bnd: int,
        bottom_row_bnd: int,
        left_col_bnd: int,
        right_col_bnd: int,
        destination_row: int,
        destination_col: int,
        array: np.darray,
    ) -> None:
        # Loop through the array to calculate Euclidean distance from the current cell to the goal cell
        for row in range(top_row_bnd, bottom_row_bnd):
            for col in range(left_col_bnd, right_col_bnd):
                row_diff = row - destination_row
                col_diff = col - destination_col
                hyp = row_diff * row_diff + col_diff * col_diff
                array[row][col] += hyp

    # Converts a numpy array into a location aware image file.  Should work with QGIS
    def write_raster(
        image_file_type: str,  # file extension,  .png, .tif, .jpg, etc.
        file_name: str,
        folder_dest: str,
        map_projection: str,  # well known name of the projection you want to use
        pixel_size: int,
        x_offset: float,
        y_offset: float,
        easting: float,
        northing: float,
        numpy_array: np.darray,
    ) -> None:
        # Calculate the insertion point on the real world map
        ew = easting + x_offset
        ns = northing + y_offset

        # Convert the numpy array into an image file using the Python imagery library.  Try to stick with a
        # lossless format.  Lossy formats like .jpg probably work but may be usuitable for certain applications
        raster = Image.fromarray(numpy_array)
        raster.save(folder_dest + file_name + image_file_type)

        # World file is a just a glorified text file that tells the system where/how to load the image file
        # on the real world map.  The order of the lines matters.
        wrld_file = open(folder_dest + file_name + ".tfw", "w")
        wrld_file.write(str(pixel_size) + "\n")  # Resolution along x axis
        wrld_file.write(str(0) + "\n")  # Rotation 1
        wrld_file.write(
            str(0) + "\n"
        )  # Rotation 2 - Not sure why there are two, maybe for geographic (non-projected coordinate systems)
        wrld_file.write(str(-1 * pixel_size) + "\n")  # resolution along y axis
        wrld_file.write(str(ew) + "\n")  # insertion point on the x axis
        wrld_file.write(str(ns) + "\n")  # insertion point on the y axis
        wrld_file.write(str(map_projection) + "\n")

        wrld_file.close()
