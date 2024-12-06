import { configureStore } from '@reduxjs/toolkit';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';
import dashboardReducer from './slices/dashboardSlice';
import riskManagementReducer from './slices/riskManagementSlice';
import assetReducer from './slices/assetSlice';

export const store = configureStore({
  reducer: {
    dashboard: dashboardReducer,
    riskManagement: riskManagementReducer,
    asset: assetReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
