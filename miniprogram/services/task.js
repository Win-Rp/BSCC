const env = require("../config/env");

function startPolling(fetcher, options) {
  const config = Object.assign(
    {
      interval: env.pollingInterval,
      immediate: true,
      shouldStop() {
        return false;
      },
      onSuccess() {},
      onError() {}
    },
    options || {}
  );

  let timer = null;
  let stopped = false;

  function stop() {
    stopped = true;
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function next() {
    if (stopped) {
      return;
    }
    Promise.resolve(fetcher())
      .then((response) => {
        config.onSuccess(response);
        if (stopped || config.shouldStop(response)) {
          return;
        }
        timer = setTimeout(next, config.interval);
      })
      .catch((error) => {
        config.onError(error);
        if (stopped) {
          return;
        }
        timer = setTimeout(next, config.interval);
      });
  }

  if (config.immediate) {
    next();
  } else {
    timer = setTimeout(next, config.interval);
  }

  return {
    stop
  };
}

function isTaskTerminal(status) {
  const value = status || "";
  return value === "awaiting_payment" || value === "completed" || value === "failed";
}

function isOrderTerminal(status) {
  const value = status || "";
  return value === "paid" || value === "closed";
}

module.exports = {
  startPolling,
  isTaskTerminal,
  isOrderTerminal
};
