噪声抑制模型 (NSNet)
====================

:link_to_translation:`en:[English]`

NSNet 是一个基于深度学习的噪声抑制模型，面向低功耗嵌入式 MCU。

概述
----

当前的 NSNet 模型为 ``nsnet2``，是一个量化后的神经网络降噪模型，具有以下特点：

- 采样率：16 kHz，16-bit PCM
- 帧长：1024 个采样点（64 ms），帧移：512 个采样点（32 ms）
- 基于 ERB 的频谱掩码：网络估计时频掩码并应用于带噪频谱
- 支持单通道处理，并支持多通道共享掩码模式（见下文 **多通道共享掩码处理**）
- 支持芯片：ESP32-S3、ESP32-S31 和 ESP32-P4

.. note::

   通过 ``idf.py menuconfig`` -> ``ESP Speech Recognition`` -> ``Select noise suppression model`` -> ``Deep noise suppression v2 (nsnet2)`` 选择模型。

使用 NSNet
----------

接口定义在 ``esp_nsn_iface.h`` 中。所有操作都通过 ``esp_nsn_iface_t`` 函数表完成，函数表由模型名获取：

**基本流程（单通道）：**

1. **获取模型接口并创建实例**

   .. code-block:: c

      #include "esp_nsn_iface.h"
      #include "esp_nsn_models.h"
      #include "model_path.h"

      srmodel_list_t *models = esp_srmodel_init("model");
      char *model_name = esp_srmodel_filter(models, ESP_NSNET_PREFIX, NULL);
      const esp_nsn_iface_t *nsnet = esp_nsnet_handle_from_name(model_name);
      esp_nsn_data_t *nsnet_data = nsnet->create(model_name);

2. **处理音频帧**

   每次调用 ``process()`` 消耗并返回 ``get_samp_chunksize()`` 个采样点（512 个采样点，即 16 kHz 下一个 32 ms 帧移）：

   .. code-block:: c

      int chunk = nsnet->get_samp_chunksize(nsnet_data);  // 512 个采样点
      int16_t in[512], out[512];
      nsnet->process(nsnet_data, in, out);

3. **释放资源**

   .. code-block:: c

      nsnet->destroy(nsnet_data);

多通道共享掩码处理
------------------

对于多通道输入（例如麦克风阵列），``esp_nsn_iface_t`` 提供 ``create_mc()`` / ``process_mc()``：ERB 掩码只从参考通道估计**一次**，并应用于所有通道，因此每增加一路通道只需付出加窗/FFT/掩码施加/IFFT/重叠相加的开销，而无需再跑一次完整的网络。

.. code-block:: c

   /* 4 通道，以通道 0 作为掩码估计的参考通道 */
   esp_nsn_data_t *nsnet_data = nsnet->create_mc(model_name, 4, 0);

   int16_t *in[4]  = {ch0_in, ch1_in, ch2_in, ch3_in};   /* 每个指针指向 chunk 个采样点 */
   int16_t *out[4] = {ch0_out, ch1_out, ch2_out, ch3_out};
   nsnet->process_mc(nsnet_data, in, out);

约束与兼容性说明：

- ``channel_num`` 取值范围为 1 至 8；``ref_channel`` 必须小于 ``channel_num``。
- ``create_mc()`` / ``process_mc()`` 追加在 ``esp_nsn_iface_t`` 末尾，不支持多通道处理的模型中这两个指针为 ``NULL``，使用前请先检查（``examples/nsnet`` 应用中即是如此）。
- 单通道 ``create()`` 等价于 ``create_mc(model_name, 1, 0)``；单通道行为与之前版本保持 bit 级一致，多通道运行的通道 0 输出与相同输入的单通道运行结果 bit 级一致。

示例
----

``examples/nsnet`` 应用演示了两种接口的用法：

- **SD 卡测试**：从 SD 卡读取 16 kHz 16-bit WAV 文件，处理**所有**输入通道（当输入多于一个通道时使用 ``create_mc()`` / ``process_mc()``，以通道 0 为参考通道），将降噪后的多通道 WAV 写回，并报告 CPU 占用、实时率和内存使用情况（同时写入 SD 卡上的性能日志文件）。
- **USB_SERIAL_JTAG 流式测试**：通过 USB 串口在 PC 主机与芯片之间流式传输音频。在主机侧运行：

  .. code-block:: bash

     python3 stream_host.py --port /dev/ttyACM1 --in test_4ch_in.wav --out out.wav

  主机发送交织排布的 16 kHz 16-bit 音频帧（每帧每通道 512 个采样点），并读回降噪后的帧；输出 WAV 保留处理后的通道数。

资源消耗
--------

在 ESP32-P4 @ 400 MHz 上实测，每 32 ms 帧（512 个采样点）：

.. list-table::
   :header-rows: 1
   :widths: 30 25 25

   * - 通道数
     - 每帧耗时 (us)
     - CPU 占用 (%)
   * - 1
     - 4534
     - 14.2
   * - 4（共享掩码）
     - 6476
     - 20.2

.. note::

   - 采用共享掩码模式时，4 通道的处理时间仅为单通道的约 1.43 倍，远小于运行 4 个独立实例的开销。
   - 模型的一般资源占用情况参见 :doc:`资源占用 <../benchmark/README>`。
