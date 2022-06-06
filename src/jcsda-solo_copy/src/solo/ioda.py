#
# ioda.py
#
# IODAv2 concatenation utility using numpy and netCDF4
#
import os
import time

import numpy
from pathlib import Path
from netCDF4 import Dataset
from numpy import ma
from solo.logger import Logger

__all__ = ['Ioda']

logger = Logger(__name__.split('.')[-1])


class Ioda(object):
    """
    Provides the utility to use numpy and netCDF4 to concatenate multiple netCDF files and to check for valid
    netCDF file extensions.
    """

    def __init__(self, name):
        self._name = name

    _VALID_SUFFIXS = {'.nc', '.nc4'}

    @classmethod
    def is_netcdf_file(cls, file_path):
        return Path(file_path).suffix.lower() in cls._VALID_SUFFIXS

    @classmethod
    def concat_files(cls, *args):
        return cls._concat_files_numpy(*args)

    @staticmethod
    def _filter_input_file(in_file):
        if os.stat(in_file).st_size == 0:
            return False
        return True

    @classmethod
    def _concat_files_numpy(cls, in_files, output):
        """
        in_files - list of paths to files to concatenate
        output - Path to output file to write
        Creates a single IODAv2 file with concatenation of all data using numpy and netCDF4
        """

        # Check input files for existence
        if not len(in_files):
            raise ValueError('There were no input netCDF source files provided.')

        # Check output file path
        if not len(output):
            raise ValueError('Output netCDF target is empty.')

        # Check output file path extension
        if not cls.is_netcdf_file(output):
            raise ValueError('Output netCDF target is not a netCDF file.')

        # Filter input files
        in_files = list(filter(Ioda._filter_input_file, in_files))

        # Create a dict for converting from numpy to netCDF data types
        numpy_to_netcdf_dtype = {numpy.dtype('float64'): 'f8',
                                 numpy.dtype('float32'): 'f4',
                                 numpy.dtype('int64'): 'i8',
                                 numpy.dtype('int32'): 'i4',
                                 numpy.dtype('S1'): 'c',
                                 numpy.dtype('object'): 'str'}

        # Get the start time
        start_time = time.time()

        # Sort the input files and initialize data structures
        in_files.sort()

        # Dict for storing the raw data arrays from the input files
        in_file_data_arrays = {}

        # Dict for storing the concatenated data arrays
        data_arrays_concat = {}

        # Dict for storing the data arrays for direct copies from the VarMetaData group
        varmetadata_data_arrays = {}

        # Dict for storing the data arrays for direct copies from the RecMetaData group
        recmetadata_data_arrays = {}

        # Then cycle over the input files and initialize keys for dict data structures
        # excluding VarMetaData and RecMetaData
        for in_file in in_files:
            input_dataset = Dataset(in_file, "r")
            in_file_data_arrays[in_file] = {}
            for group in input_dataset.groups:
                if group != 'VarMetaData' and group != 'RecMetaData':
                    in_file_data_arrays[in_file][group] = {}
                    for variable in input_dataset[group].variables:
                        in_file_data_arrays[in_file][group][variable] = None
            input_dataset.close()

        # Open the output data file as a Dataset and the first input data file as a template
        output_dataset = Dataset(output, "w")
        input_dataset_template = Dataset(in_files[0], "r")

        # Copy all root group attributes to the output file
        for attribute in input_dataset_template.ncattrs():
            output_dataset.setncattr(attribute, input_dataset_template.getncattr(attribute))

        # Cycle over all groups in the template
        for group in input_dataset_template.groups:

            # Create all of the groups in the output data file
            output_dataset.createGroup(group)

            # For all groups besides VarMetaData and RecMetaData, add variables to the concat data structure
            if group != 'VarMetaData' and group != 'RecMetaData':
                data_arrays_concat[group] = {}
                for variable in input_dataset_template[group].variables:
                    data_array_template = input_dataset_template[group].variables[variable][:]
                    data_arrays_concat[group][variable] = data_array_template.real
            # Add variables to the VarMetaData data structure
            elif group == 'VarMetaData':
                for variable in input_dataset_template[group].variables:
                    data_array_template = input_dataset_template[group].variables[variable][:]
                    varmetadata_data_arrays[variable] = data_array_template.real
            # Add variables to the RecMetaData data structure
            elif group == 'RecMetaData':
                for variable in input_dataset_template[group].variables:
                    data_array_template = input_dataset_template[group].variables[variable][:]
                    recmetadata_data_arrays[variable] = data_array_template.real

        # Cycle over all dimensions in the template
        for dim in input_dataset_template.dimensions:

            # If the dimension is not nlocs, then create the dimension in the output data file and fill
            # with a range of 1 to size+1
            if dim != 'nlocs':
                name = input_dataset_template.dimensions[dim].name
                size = input_dataset_template.dimensions[dim].size
                output_dataset.createDimension(name, size)
                output_dataset.createVariable(name, 'int32', (name,))
                output_dataset.variables[dim].setncattr('suggested_chunk_dim', size)
                output_dataset.variables[dim][:] = numpy.arange(1, size + 1, 1, dtype='int32')

            # If the dimension is nchans, copy nchans from the template to the output data file
            if dim == 'nchans':
                nchans_data_array = input_dataset_template['nchans'][:].real
                output_dataset.variables['nchans'][:] = nchans_data_array

        # Get the total nlocs value from the input data files, create that
        # dimension in the output data file, and fill with a range of 1 to size+1
        nlocs_total_size = 0
        for in_file in in_files:
            in_file_dataset = Dataset(in_file, 'r')
            for dim in in_file_dataset.dimensions:
                if dim == 'nlocs':
                    nlocs_total_size += in_file_dataset.dimensions['nlocs'].size
                    break
            in_file_dataset.close()
        output_dataset.createDimension('nlocs', nlocs_total_size)
        output_dataset.createVariable('nlocs', 'int32', ('nlocs',))
        output_dataset.variables['nlocs'].setncattr('suggested_chunk_dim', nlocs_total_size)
        output_dataset.variables['nlocs'][:] = numpy.arange(1, nlocs_total_size + 1, 1, dtype='int32')

        # Cycle over all variables in the input data files and collect the raw data
        # keyed on in_file, group, and variable except for the VarMetaData and RecMetaData groups
        for in_file in in_files:
            input_dataset = Dataset(in_file, 'r')
            for group in input_dataset.groups:
                if group != 'VarMetaData' and group != 'RecMetaData':
                    for variable in input_dataset[group].variables:
                        data_array = input_dataset[group].variables[variable][:]
                        in_file_data_arrays[in_file][group][variable] = data_array.real
            input_dataset.close()

        # Cycle over all variables in the input data files and concatenate the raw data
        # except for the VarMetaData and RecMetaData groups
        for in_file in in_files:
            if in_file != in_files[0]:
                input_dataset = Dataset(in_file, 'r')
                for group in input_dataset.groups:
                    if group != 'VarMetaData' and group != 'RecMetaData':
                        for variable in input_dataset[group].variables:
                            a = data_arrays_concat[group][variable]
                            b = in_file_data_arrays[in_file][group][variable]
                            data_arrays_concat[group][variable] = ma.concatenate((a, b))
                input_dataset.close()

        # Cycle over concatenated data arrays, create all variables with the nlocs or nlocs + nchans dimensions,
        # and write the concatenated data arrays to the output data file
        for group in data_arrays_concat.keys():
            for variable in data_arrays_concat[group].keys():
                data_array = data_arrays_concat[group][variable]
                dtype = numpy_to_netcdf_dtype[data_array.dtype]
                name = f'/{group}/{variable}'
                if name == '/MetaData/channelNumber':
                    dims = 'nchans'
                    data_array = output_dataset.variables['nchans'][:].real
                elif len(data_array.shape) == 1:
                    dims = 'nlocs'
                elif len(data_array.shape) == 2:
                    dims = ('nlocs', 'nchans')
                output_dataset.createVariable(name, dtype, dims)
                output_dataset[name][:] = data_array

        # Cycle over variables in the VarMetaData data structure, create the variables,
        # and write the data arrays to the output data file
        for variable in varmetadata_data_arrays:
            data_array = varmetadata_data_arrays[variable]
            dtype = numpy_to_netcdf_dtype[data_array.dtype]
            name = f'/VarMetaData/{variable}'
            dims = input_dataset_template[name].dimensions
            output_dataset.createVariable(name, dtype, dims)
            output_dataset[name][:] = data_array

        # Cycle over variables in the RecMetaData data structure, create the variables,
        # and write the data arrays to the output data file
        for variable in recmetadata_data_arrays:
            data_array = recmetadata_data_arrays[variable]
            dtype = numpy_to_netcdf_dtype[data_array.dtype]
            name = f'/RecMetaData/{variable}'
            dims = input_dataset_template[name].dimensions
            output_dataset.createVariable(name, dtype, dims)
            output_dataset[name][:] = data_array

        # Cycle over groups and variables to copy attributes to the output file (skips _FillValue)
        for group in input_dataset_template.groups:
            for variable in input_dataset_template[group].variables:
                name = f'/{group}/{variable}'
                for attribute in input_dataset_template[name].ncattrs():
                    if attribute != '_FillValue':
                        output_dataset[name].setncattr(attribute, input_dataset_template[name].getncattr(attribute))

        # Close the template data file
        input_dataset_template.close()

        # Close the output data file
        output_dataset.close()

        # Log time statistics
        elapsed_time = time.time() - start_time
        logger.info(f'output: {output} - number of input files: {len(in_files)}')
        logger.info(f'elapsed[concat and write]:{elapsed_time:.3g}s')
