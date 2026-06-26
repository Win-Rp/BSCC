import * as echarts from "echarts";
import type { ECharts, EChartsOption } from "echarts";
import { nextTick, onBeforeUnmount, ref, toRaw, type Ref } from "vue";

export function useEChart(container: Ref<HTMLElement | undefined>) {
  const chart = ref<ECharts>();

  const render = async (option: EChartsOption) => {
    await nextTick();
    if (!container.value) return;
    chart.value ??= echarts.init(container.value);
    chart.value.clear();
    chart.value.setOption(toRaw(option), { notMerge: true, lazyUpdate: false });
  };

  const resize = () => chart.value?.resize();

  window.addEventListener("resize", resize);
  onBeforeUnmount(() => {
    window.removeEventListener("resize", resize);
    chart.value?.dispose();
  });

  return { chart, render, resize };
}
