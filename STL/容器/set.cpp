std::set 是 C++ STL（标准模板库）中的有序、唯一元素集合容器，底层基于红黑树（一种自平衡二叉搜索树）实现，核心特性是：元素自动排序且无重复，支持高效的插入、删除、查找操作（平均时间复杂度 O(logn)）。
1. 核心特性
•	有序性：元素默认按升序排列（可自定义排序规则），遍历结果始终有序；
•	唯一性：容器中不会存在重复元素，插入重复值会被自动忽略；
•	动态大小：内存分配在堆上，大小可动态增减，无需提前指定；
•	非随机访问：不支持下标（[]）访问，需通过迭代器遍历或 find() 查找元素；
•	底层实现：红黑树保证了插入 / 删除 / 查找的高效性，且迭代器稳定性（删除元素时仅指向该元素的迭代器失效，其余迭代器仍可用）。
•	2. 基本用法
•	（1）头文件与声明
•	使用 std::set 必须包含头文件 <set>，声明格式为：
•	cpp
•	运行
•	#include <set>  // 必须包含的头文件
•	
•	// 语法：std::set<元素类型, 排序规则> 容器名;
•	std::set<int> s1;  // 默认升序的int类型set
•	std::set<int, std::greater<int>> s2;  // 自定义降序的int类型set
•	std::set<std::string> s3;  // 存储字符串的set（默认按字符串字典序排序）
（2）核心成员函数
函数	功能
insert(val)	插入元素 val，成功返回 pair<iterator, bool>（迭代器 + 是否插入成功）；重复元素返回 bool=false
erase(pos)	删除迭代器 pos 指向的元素，无返回值
erase(val)	删除值为 val 的元素，返回被删除的元素个数（set 中仅 0 或 1）
erase(beg, end)	删除 [beg, end) 区间内的元素，无返回值
find(val)	查找值为 val 的元素，找到返回指向该元素的迭代器，否则返回 end()
count(val)	统计值为 val 的元素个数（set 中仅 0 或 1，可用于判断元素是否存在）
size()	返回容器中元素的个数
empty()	判断容器是否为空（空返回 true）
clear()	清空容器中所有元素
begin()/end()	返回指向第一个 / 末尾后一位的迭代器（正向遍历）
rbegin()/rend()	返回指向最后一个 / 第一个前一位的反向迭代器（反向遍历）
lower_bound(val)	返回第一个大于等于 val 的元素迭代器
upper_bound(val)	返回第一个大于 val 的元素迭代器
	
//-----------------------------------------------------------------------------
#include <iostream>
#include <set>   // std::set 头文件
#include <string>

int main() {
    // 1. 初始化与插入
    std::set<int> s;
    // 插入元素（返回pair：first=迭代器，second=是否插入成功）
    auto ret1 = s.insert(3);  // 插入3，成功，ret1.second=true
    auto ret2 = s.insert(1);  // 插入1，成功
    auto ret3 = s.insert(5);  // 插入5，成功
    auto ret4 = s.insert(3);  // 插入重复值3，失败，ret4.second=false

    std::cout << "插入3是否成功：" << (ret4.second ? "是" : "否") << std::endl;  // 输出：否

    // 2. 基础属性
    std::cout << "set大小：" << s.size() << std::endl;  // 输出：3（元素为1,3,5）
    std::cout << "set是否为空：" << (s.empty() ? "是" : "否") << std::endl;  // 输出：否

    // 3. 遍历（默认升序）
    std::cout << "正向遍历（升序）：";
    for (auto it = s.begin(); it != s.end(); ++it) {
        std::cout << *it << " ";  // 输出：1 3 5
    }
    std::cout << std::endl;

    // 反向遍历（降序）
    std::cout << "反向遍历（降序）：";
    for (auto it = s.rbegin(); it != s.rend(); ++it) {
        std::cout << *it << " ";  // 输出：5 3 1
    }
    std::cout << std::endl;

    // 4. 查找与计数
    int target = 3;
    auto it = s.find(target);
    if (it != s.end()) {
        std::cout << "找到元素：" << *it << std::endl;  // 输出：找到元素：3
    } else {
        std::cout << "未找到元素：" << target << std::endl;
    }

    int cnt = s.count(3);  // 统计3的个数，set中仅0或1
    std::cout << "元素3的个数：" << cnt << std::endl;  // 输出：1

    // 5. 自定义排序（降序set）
    std::set<int, std::greater<int>> s_desc;
    s_desc.insert({1, 2, 3, 4, 5});
    std::cout << "降序set遍历：";
    for (int num : s_desc) {  // 范围for遍历（C++11+）
        std::cout << num << " ";  // 输出：5 4 3 2 1
    }
    std::cout << std::endl;

    // 6. 删除元素
    s.erase(1);  // 删除值为1的元素
    std::cout << "删除1后size：" << s.size() << std::endl;  // 输出：2（剩余3,5）

    auto it_del = s.find(5);
    if (it_del != s.end()) {
        s.erase(it_del);  // 通过迭代器删除5
    }
    std::cout << "删除5后size：" << s.size() << std::endl;  // 输出：1（剩余3）

    // 7. 清空容器
    s.clear();
    std::cout << "清空后是否为空：" << (s.empty() ? "是" : "否") << std::endl;  // 输出：是

    return 0;
}
//-----------------------------------------------------------------------------
#include<set>
#include<iostream>
using namespace std;

int main()
{
    set<int> s1;
    s1.insert(3);
    s1.insert(1);
    s1.insert(5);
   // auto a = s1.find(5);
    //cout << *a;// 解引用迭代器，获取指向的元素值
    for (auto it = s1.begin(); it != s1.end(); ++it) {
        std::cout << *it << " ";  // 输出：1 3 5
    }//s1.begin()：返回指向第一个有效元素的迭代器（本例中指向值为 1 的元素）；
    //s1.end()：返回指向最后一个有效元素的下一个位置的迭代器（称为 “尾后迭代器”），不指向任何有效元素。
    return 0;
}
//-----------------------------------------------------------------------------
