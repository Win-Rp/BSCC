declare module "mark.js" {
  interface MarkOptions {
    acrossElements?: boolean;
    className?: string;
    done?: () => void;
    separateWordSearch?: boolean;
  }

  export default class Mark {
    constructor(context: Element | Element[] | NodeList | HTMLElement);
    mark(keyword: string, options?: MarkOptions): void;
    unmark(options?: { done?: () => void }): void;
  }
}
