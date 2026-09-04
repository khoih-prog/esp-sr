Noise Suppression Model (NSNet)
================================

:link_to_translation:`zh_CN:[中文]`

NSNet is a deep-learning-based noise suppression model for low-power embedded MCUs.

Overview
--------

The current NSNet model is ``nsnet2``, a quantized neural noise suppression model with the following features:

- Sample rate: 16 kHz, 16-bit PCM
- Frame length: 1024 samples (64 ms), frame shift: 512 samples (32 ms)
- ERB-based spectral masking: the network estimates a time-frequency mask which is applied to the noisy spectrum
- Single-channel processing, plus a multi-channel shared-mask mode (see **Multi-Channel Shared-Mask Processing** below)
- Supported chips: ESP32-S3, ESP32-S31 and ESP32-P4

.. note::

   Select the model via ``idf.py menuconfig`` -> ``ESP Speech Recognition`` -> ``Select noise suppression model`` -> ``Deep noise suppression v2 (nsnet2)``.

Use NSNet
---------

The interface is defined in ``esp_nsn_iface.h``. All operations go through the ``esp_nsn_iface_t`` function table, which is obtained from the model name:

**Basic Flow (single channel):**

1. **Get the model interface and create an instance**

   .. code-block:: c

      #include "esp_nsn_iface.h"
      #include "esp_nsn_models.h"
      #include "model_path.h"

      srmodel_list_t *models = esp_srmodel_init("model");
      char *model_name = esp_srmodel_filter(models, ESP_NSNET_PREFIX, NULL);
      const esp_nsn_iface_t *nsnet = esp_nsnet_handle_from_name(model_name);
      esp_nsn_data_t *nsnet_data = nsnet->create(model_name);

2. **Process audio frames**

   Each call to ``process()`` consumes and returns ``get_samp_chunksize()`` samples (512 samples, i.e. one 32 ms frame shift at 16 kHz):

   .. code-block:: c

      int chunk = nsnet->get_samp_chunksize(nsnet_data);  // 512 samples
      int16_t in[512], out[512];
      nsnet->process(nsnet_data, in, out);

3. **Release resources**

   .. code-block:: c

      nsnet->destroy(nsnet_data);

Multi-Channel Shared-Mask Processing
------------------------------------

For multi-channel inputs (e.g., a microphone array), ``esp_nsn_iface_t`` provides ``create_mc()`` / ``process_mc()``: the ERB mask is estimated **once** from the reference channel and applied to every channel, so each additional channel only costs windowing/FFT/mask-application/IFFT/overlap-add instead of a full network pass.

.. code-block:: c

   /* 4 channels, channel 0 as the reference for mask estimation */
   esp_nsn_data_t *nsnet_data = nsnet->create_mc(model_name, 4, 0);

   int16_t *in[4]  = {ch0_in, ch1_in, ch2_in, ch3_in};   /* each entry: chunk samples */
   int16_t *out[4] = {ch0_out, ch1_out, ch2_out, ch3_out};
   nsnet->process_mc(nsnet_data, in, out);

Constraints and compatibility notes:

- ``channel_num`` ranges from 1 to 8; ``ref_channel`` must be smaller than ``channel_num``.
- ``create_mc()`` / ``process_mc()`` are appended at the end of ``esp_nsn_iface_t`` and are ``NULL`` for models that do not support multi-channel processing — check them before use (as done in the ``examples/nsnet`` application).
- The single-channel ``create()`` is equivalent to ``create_mc(model_name, 1, 0)``; single-channel behavior is bit-exact with previous versions, and channel 0 of a multi-channel run is bit-identical to a single-channel run of the same input.

Examples
--------

The ``examples/nsnet`` application demonstrates both interfaces:

- **SD card test**: reads a 16 kHz 16-bit WAV file from the SD card, processes **all** input channels (using ``create_mc()`` / ``process_mc()`` when the input has more than one channel, with channel 0 as the reference), writes the enhanced multi-channel WAV back, and reports CPU load, real-time factor and memory usage (also written to a performance log file on the SD card).
- **USB_SERIAL_JTAG streaming test**: streams audio between a host PC and the chip over the USB serial interface. On the host side, run:

  .. code-block:: bash

     python3 stream_host.py --port /dev/ttyACM1 --in test_4ch_in.wav --out out.wav

  The host sends interleaved 16 kHz 16-bit frames (512 samples per channel per frame) and reads back the enhanced frames; the output WAV keeps the processed channel count.

Resource Consumption
--------------------

Measured on ESP32-P4 @ 400 MHz, per 32 ms frame (512 samples):

.. list-table::
   :header-rows: 1
   :widths: 30 25 25

   * - Channels
     - Time per Frame (us)
     - CPU Usage (%)
   * - 1
     - 4534
     - 14.2
   * - 4 (shared mask)
     - 6476
     - 20.2

.. note::

   - With the shared-mask mode, 4 channels cost only about 1.43x the single-channel processing time, far less than running 4 independent instances.
   - For general model resource occupancy, see :doc:`Resource Occupancy <../benchmark/README>`.
