import useWebApp from './useWebApp';

/**
 * {@link telegram!WebAppUser}
 */
export type WebAppUser = {
  id: number;
  is_bot?: boolean;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  photo_url?: string;
  is_premium?: boolean;
  added_to_attachment_menu?: true;
  allows_write_to_pm?: true;
};

export type InitData = string;

/**
 * {@link telegram!WebAppInitData}
 */
export type InitDataUnsafe = {
  query_id?: string;
  user?: WebAppUser;
  receiver?: WebAppUser;
  chat_instance?: string;
  start_param?: string;
  auth_date: number;
  hash: string;
  can_send_after?: number;
};

const useInitData = (): readonly [
  InitDataUnsafe | undefined,
  InitData | undefined,
] => {
  const WebApp = useWebApp();

  return [WebApp?.initDataUnsafe, WebApp?.initData] as const;
};

export default useInitData;