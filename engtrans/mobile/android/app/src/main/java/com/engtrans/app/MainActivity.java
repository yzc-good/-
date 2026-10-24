package com.engtrans.app;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    {
        // 注册远程更新插件（在 super.onCreate 加载插件之前加入）
        initialPlugins.add(UpdateManager.class);
    }
}