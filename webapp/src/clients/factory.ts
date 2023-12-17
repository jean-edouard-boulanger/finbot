import { APP_SERVICE_ENDPOINT } from "utils/env-config";
import { Configuration, Middleware, ResponseContext } from "./app-client";

export type Constructible<
  Params extends readonly any[] = any[],
  T = any,
> = new (...params: Params) => T;

export type ResponseHandler = (response: Response) => void;

class SubscriptionHandle {
  private id: number;
  private handler: ResponseHandler;

  public constructor(id: number, handler: ResponseHandler) {
    this.id = id;
    this.handler = handler;
  }

  public getId(): number {
    return this.id;
  }

  public getHandler(): ResponseHandler {
    return this.handler;
  }
}

class GlobalResponseListener {
  private static instance: GlobalResponseListener;
  private subscriptions: Array<SubscriptionHandle>;
  private lastId: number;

  private constructor() {
    this.subscriptions = [];
    this.lastId = 0;
  }

  public static getInstance(): GlobalResponseListener {
    if (!GlobalResponseListener.instance) {
      GlobalResponseListener.instance = new GlobalResponseListener();
    }
    return GlobalResponseListener.instance;
  }

  public subscribe(handler: ResponseHandler): SubscriptionHandle {
    const subscription = new SubscriptionHandle(this.lastId++, handler);
    this.subscriptions.push(subscription);
    return subscription;
  }

  public unsubscribe(subscription: SubscriptionHandle): void {
    this.subscriptions = this.subscriptions.filter(
      (item) => item.getId() !== subscription.getId(),
    );
  }

  public dispatchResponse(context: ResponseContext): void {
    for (const subscription of this.subscriptions) {
      try {
        subscription.getHandler()(context.response);
      } catch (e) {
        console.error(
          `failure while updating subscription ${subscription.getId()}: ${e}`,
        );
      }
    }
  }
}

const appMiddleware: Middleware = {
  post: async (context: ResponseContext) => {
    GlobalResponseListener.getInstance().dispatchResponse(context);
    if (context.response.ok) {
      return;
    }
    let payload = null;
    try {
      payload = await context.response.json();
    } catch (e) {
      return;
    }
    if (payload && "error" in payload) {
      throw new Error(payload.error.user_message);
    }
  },
};

export function makeApi<ApiT extends Constructible>(
  apiType: ApiT,
  jwtToken?: string,
): InstanceType<ApiT> {
  const serverUrl = APP_SERVICE_ENDPOINT?.replace("/api/v1", "");
  return new apiType(
    new Configuration({
      accessToken: jwtToken,
      basePath: serverUrl,
      middleware: [appMiddleware],
    }),
  );
}

export class ResponseInterceptor {
  handle: SubscriptionHandle | null;

  public constructor() {
    this.handle = null;
  }

  public subscribe(handler: ResponseHandler): void {
    this.handle = GlobalResponseListener.getInstance().subscribe(handler);
  }

  public unsubscribe(): void {
    if (this.handle) {
      GlobalResponseListener.getInstance().unsubscribe(this.handle);
    }
  }
}
